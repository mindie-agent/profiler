# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "21c30821d87a757bace8cf6b2fffea2536db643e"}.

Variant: `a3-retained-cohort-service-21c30821`. Baseline: null.

Sim 0.8.0; 288 package files; SHA256 `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 39.112085 | 39.104879 | 39.195917 | 33.636900 | -14.00% | compared |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 33.636900 | -13.65% | compared |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 40.969878 | 40.934812 | 41.046340 | 35.482501 | -13.39% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 6.713782 | 6.664787 | 6.922921 | 6.063596 | -9.68% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3 | 3.240302 | 3.278234 | 3.410932 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3 | 3.363853 | 3.379593 | 3.466951 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 3.812064 | 3.812064 | 3.812064 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2.978001 | 2.978001 | 2.978001 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 4.690486 | 4.690486 | 4.690486 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 9.615404 | 9.549549 | 9.774245 | 8.639061 | -10.15% | compared |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3 | 3.178496 | 3.253895 | 3.501150 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 2 | 8.472921 | 8.472921 | 8.559829 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 2 | 5.631388 | 5.631388 | 5.719806 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 2 | 4.722715 | 4.722715 | 4.738645 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 3.160037 | 3.160037 | 3.160037 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 3.536929 | 3.536929 | 3.536929 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 34.118460 | 33.910318 | 35.073041 | 30.600588 | -10.31% | compared |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 12 | 33.269101 | 33.259625 | 33.460529 | — | — | unresolved: prediction_deferred_by_population_priority |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 32.485961 | 32.416312 | 32.734306 | 29.272304 | -9.89% | compared |
| v4flash-a3-tp8-c4:q2_b1_m2 | 4 | 29.500360 | 29.511530 | 29.660627 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.112085 | 37.273101 | 1.838985 | 4.70% | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | 37.243385 | 1.711442 | 4.39% | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.969878 | 39.246789 | 1.723088 | 4.21% | not_established | 8 / 1 / 1 | auto / full |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.713782 | 6.584489 | 0.129293 | 1.93% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3.240302 | 3.098912 | 0.141390 | 4.36% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3.363853 | 3.219977 | 0.143876 | 4.28% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 3.812064 | 3.685928 | 0.126136 | 3.31% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 2.978001 | 2.829064 | 0.148937 | 5.00% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 4.690486 | 4.563168 | 0.127318 | 2.71% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 9.615404 | 9.483330 | 0.132074 | 1.37% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3.178496 | 3.036799 | 0.141698 | 4.46% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 8.472921 | 8.341965 | 0.130956 | 1.55% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 5.631388 | 5.506011 | 0.125376 | 2.23% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 4.722715 | 4.591257 | 0.131459 | 2.78% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 3.160037 | 3.018060 | 0.141977 | 4.49% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 3.536929 | 3.398233 | 0.138696 | 3.92% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 34.118460 | 32.625252 | 1.493208 | 4.38% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 33.269101 | 31.831689 | 1.437413 | 4.32% | not_established | 16 / 1 / 16 | none / full |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.485961 | 30.611484 | 1.874477 | 5.77% | not_established | 8 / 1 / 8 | none / full |
| v4flash-a3-tp8-c4:q2_b1_m2 | 29.500360 | 27.578127 | 1.922233 | 6.52% | not_established | 8 / 1 / 8 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.396276 | 0.393697 | 0.402033 | 0.353843 | -10.71% |
| a3_glm53_dc16k_b1:q1_b1_m1 | moe_layer | 52 / 75 | 0.504482 | 0.483485 | 0.576161 | 0.434338 | -13.90% |
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.353843 | -8.69% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 55 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.434338 | -13.66% |
| a3_glm53_dc4k_b2:q1_b2_m2 | dense_layer | 3 / 3 | 0.403290 | 0.407802 | 0.410515 | 0.355317 | -11.90% |
| a3_glm53_dc4k_b2:q1_b2_m2 | moe_layer | 57 / 75 | 0.529285 | 0.509096 | 0.601701 | 0.458887 | -13.30% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | dense_layer | 0 / 1 | 0.838259 | 0.838259 | 0.838259 | 0.687241 | -18.02% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | moe_layer | 2 / 3 | 1.958234 | 1.906321 | 2.172615 | 1.772012 | -9.51% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | dense_layer | 0 / 1 | 0.862610 | 0.862610 | 0.862610 | 0.705247 | -18.24% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | moe_layer | 3 / 3 | 2.917340 | 2.803217 | 3.209222 | 2.629776 | -9.86% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | dense_layer | 0 / 3 | 0.588732 | 0.573221 | 0.632444 | 0.382288 | -35.07% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | moe_layer | 40 / 42 | 0.769068 | 0.710639 | 0.953812 | 0.701279 | -8.81% |
| v4flash-a3-tp8-c4:q2_b4_m8 | moe_layer | 41 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.680751 | -9.75% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 55 / 78 | 0.500321 | 0.482807 | 0.576161 | 0.431242 | -13.81% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 58 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.431242 | -13.51% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 60 / 78 | 0.524439 | 0.508658 | 0.601701 | 0.454904 | -13.26% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 / 3 | 1.513448 | 1.795764 | 1.906321 | 1.413230 | -6.62% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 0 / 1 | 2.172615 | 2.172615 | 2.172615 | 1.763585 | -18.83% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 / 3 | 2.135136 | 2.739582 | 2.803217 | 1.955286 | -8.42% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 / 1 | 3.209222 | 3.209222 | 3.209222 | 2.728717 | -14.97% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 30 / 34 | 0.693117 | 0.694880 | 0.733617 | 0.632019 | -8.81% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 10 / 11 | 0.954644 | 0.951023 | 0.969821 | 0.828358 | -13.23% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 41 / 43 | 0.754333 | 0.756827 | 0.850173 | 0.680751 | -9.75% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 0.500321 | 0.477860 | 0.022460 |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | 0.477479 | 0.021151 |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 0.524439 | 0.503164 | 0.021275 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 1.513448 | 1.488582 | 0.024866 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 2.172615 | 2.118742 | 0.053873 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2.135136 | 2.109379 | 0.025757 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 3.209222 | 3.155193 | 0.054029 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 0.693117 | 0.662930 | 0.030187 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 0.954644 | 0.916877 | 0.037767 |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 0.754333 | 0.711895 | 0.042438 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | all | 77 | 5698 | 0.501597 | 0.482860 | 0.421012 | -12.81% |
| a3_glm53_dc16k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.501597 | 0.482860 | 0.421012 | -12.81% |
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.421012 | -13.13% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.421012 | -13.13% |
| a3_glm53_dc4k_b2:q1_b2_m2 | all | 77 | 5390 | 0.525918 | 0.508590 | 0.445452 | -12.41% |
| a3_glm53_dc4k_b2:q1_b2_m2 | mla | 77 | 5390 | 0.525918 | 0.508590 | 0.445452 | -12.41% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | all | 3 | 660 | 1.958234 | 1.879452 | 1.776225 | -5.49% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 | 440 | 1.851043 | 1.837689 | 1.776225 | -3.34% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 | 220 | 2.172615 | 2.172336 | 1.763585 | -18.82% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | all | 3 | 588 | 2.917340 | 2.774904 | 2.580306 | -7.01% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 | 392 | 2.771399 | 2.756885 | 2.580306 | -6.41% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 | 196 | 3.209222 | 3.208946 | 2.728717 | -14.97% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | all | 44 | 2024 | 0.761223 | 0.671958 | 0.656187 | -2.35% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | kda | 33 | 1518 | 0.696750 | 0.664003 | 0.656187 | -1.18% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | mla | 11 | 506 | 0.954644 | 0.939519 | 0.828358 | -11.83% |
| v4flash-a3-tp8-c4:q2_b4_m8 | all | 42 | 4368 | 0.754274 | 0.753685 | 0.684023 | -9.24% |
| v4flash-a3-tp8-c4:q2_b4_m8 | mla | 42 | 4368 | 0.754274 | 0.753685 | 0.684023 | -9.24% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | 74 | 0.402033 | 0.396682 | 0.411171 | 0.353843 | -11.99% |
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.353843 | -10.25% |
| a3_glm53_dc4k_b2:q1_b2_m2 | 70 | 0.410515 | 0.395952 | 0.454831 | 0.355317 | -13.45% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 0.838259 | 0.793934 | 1.000700 | 0.687241 | -18.02% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 0.862610 | 0.821223 | 0.997380 | 0.705247 | -18.24% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 46 | 0.573221 | 0.501010 | 0.719194 | 0.382288 | -33.31% |
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 0.756827 | 0.717805 | 0.958641 | 0.588428 | -22.25% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc16k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 16384 | 1 | — | — | — | — |
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b2:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 2 | — | — | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 1 | 32 | 32 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 1 | 64 | 64 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 1 | 48 | 48 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 1 | 24 | 24 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 2 | 51.625998 | 45.879581 | — | 39.789500 |
| v4flash-a3-tp8-c4:q2_b4_m8 | 2 | 4 | 8 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |
| v4flash-a3-tp8-c4:q2_b1_m2 | 2 | 1 | 2 | unknown | 4096 | 4 | 53.936384 | 47.929425 | — | 39.377165 |

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
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | embedding | 220 | 0.009116 | 0.009080 | 0.009420 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | final_norm | 220 | 0.009454 | 0.009280 | 0.009460 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | lm_head | 220 | 0.313890 | 0.313543 | 0.317654 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | embedding | 3 | 0.009493 | 0.009499 | 0.009760 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | final_norm | 3 | 0.003600 | 0.003600 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | lm_head | 3 | 0.277841 | 0.276815 | 0.280234 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | embedding | 3 | 0.003020 | 0.002940 | 0.003300 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | final_norm | 3 | 0.004353 | 0.004400 | 0.004440 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | lm_head | 3 | 0.284234 | 0.285574 | 0.285794 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | embedding | 1 | 0.003660 | 0.003660 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | final_norm | 1 | 0.004940 | 0.004940 | 0.004940 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | lm_head | 1 | 0.292854 | 0.292854 | 0.292854 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | embedding | 1 | 0.002720 | 0.002720 | 0.002720 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | final_norm | 1 | 0.003840 | 0.003840 | 0.003840 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | lm_head | 1 | 0.280574 | 0.280574 | 0.280574 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | embedding | 1 | 0.005100 | 0.005100 | 0.005100 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | final_norm | 1 | 0.006300 | 0.006300 | 0.006300 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | lm_head | 1 | 0.317034 | 0.317034 | 0.317034 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | embedding | 196 | 0.009384 | 0.009360 | 0.009680 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | final_norm | 196 | 0.010675 | 0.010400 | 0.010640 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | lm_head | 196 | 0.329141 | 0.328854 | 0.332534 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | embedding | 3 | 0.008933 | 0.008899 | 0.009060 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | final_norm | 3 | 0.003567 | 0.003560 | 0.003580 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | lm_head | 3 | 0.276587 | 0.276014 | 0.279314 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | embedding | 2 | 0.006850 | 0.006850 | 0.007000 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | final_norm | 2 | 0.009080 | 0.009080 | 0.009199 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | lm_head | 2 | 0.320554 | 0.320554 | 0.320933 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | embedding | 2 | 0.006979 | 0.006979 | 0.007100 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | final_norm | 2 | 0.008540 | 0.008540 | 0.008640 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | lm_head | 2 | 0.307554 | 0.307554 | 0.309354 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | embedding | 2 | 0.005020 | 0.005020 | 0.005060 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | final_norm | 2 | 0.007720 | 0.007720 | 0.008960 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | lm_head | 2 | 0.310954 | 0.310954 | 0.311894 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | embedding | 1 | 0.002520 | 0.002520 | 0.002520 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | final_norm | 1 | 0.004000 | 0.004000 | 0.004000 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | lm_head | 1 | 0.287334 | 0.287334 | 0.287334 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | embedding | 1 | 0.002840 | 0.002840 | 0.002840 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | final_norm | 1 | 0.004400 | 0.004400 | 0.004400 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | lm_head | 1 | 0.281494 | 0.281494 | 0.281494 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | embedding | 46 | 0.004146 | 0.004110 | 0.004340 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | output_head_preparation | 46 | 0.012194 | 0.012140 | 0.012901 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | final_norm | 46 | 0.136332 | 0.134193 | 0.135443 |
| glm53flash-a3-tp16-c2:q6_b2_m12 | lm_head | 46 | 0.104697 | 0.104482 | 0.105662 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | embedding | 12 | 0.003035 | 0.003010 | 0.003080 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | output_head_preparation | 12 | 0.011463 | 0.011420 | 0.012040 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | final_norm | 12 | 0.129586 | 0.129382 | 0.131623 |
| glm53flash-a3-tp16-c2:q6_b1_m6 | lm_head | 12 | 0.092909 | 0.092882 | 0.094442 |
| v4flash-a3-tp8-c4:q2_b4_m8 | embedding | 104 | 0.003734 | 0.003720 | 0.003880 |
| v4flash-a3-tp8-c4:q2_b4_m8 | output_head_preparation | 104 | 0.492855 | 0.492950 | 0.495110 |
| v4flash-a3-tp8-c4:q2_b4_m8 | final_norm | 104 | 0.614302 | 0.614038 | 0.616248 |
| v4flash-a3-tp8-c4:q2_b4_m8 | lm_head | 104 | 0.201138 | 0.201166 | 0.201936 |
| v4flash-a3-tp8-c4:q2_b1_m2 | embedding | 4 | 0.002955 | 0.002930 | 0.003200 |
| v4flash-a3-tp8-c4:q2_b1_m2 | output_head_preparation | 4 | 0.475390 | 0.475930 | 0.477611 |
| v4flash-a3-tp8-c4:q2_b1_m2 | final_norm | 4 | 0.615858 | 0.616248 | 0.617227 |
| v4flash-a3-tp8-c4:q2_b1_m2 | lm_head | 4 | 0.200426 | 0.200636 | 0.201416 |

Summary: {"case_count": 20, "compared_cases": 7, "failed_cases": 0, "measured_cases": 20, "passed_cases": 7, "source_case_count": 7, "unresolved_cases": 13}
