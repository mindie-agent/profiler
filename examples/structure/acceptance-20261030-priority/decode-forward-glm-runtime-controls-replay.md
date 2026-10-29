# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "5935c87b"}.

Variant: `glm_indexed_owner_and_projection_controls`. Baseline: [{"path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-priority-replay.json", "runtime_source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec"}, {"path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-second-wave-replay.json", "runtime_source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec"}].

Sim 0.8.0; 227 package files; SHA256 `b79e1539e4db91ed6748c84291d9205535cdcf02befa726db8d3503836c7c1f6`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 38.954827 | 38.942772 | 39.036040 | 33.572992 | -13.82% | compared |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 47.113275 | 47.148578 | 47.401813 | 44.050191 | -6.50% | compared |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 41.069081 | 40.940238 | 41.282305 | 59.176127 | +44.09% | compared |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 16 | 33.619412 | 33.419468 | 33.979959 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 13 | 23.486220 | 23.362747 | 23.611371 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 9 | 28.226931 | 28.040600 | 29.858177 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 7 | 35.013734 | 34.765394 | 36.430748 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 6 | 37.826433 | 37.533850 | 39.879377 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 5 | 26.385455 | 25.915717 | 28.428948 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 4 | 43.281560 | 42.787796 | 45.251624 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 4 | 30.244200 | 29.664923 | 32.051220 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 3 | 35.070247 | 34.379047 | 36.534050 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 2 | 41.543810 | 41.543810 | 43.477069 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 1 | 44.811275 | 44.811275 | 44.811275 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 1 | 44.979779 | 44.979779 | 44.979779 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 9.498030 | -39.44% | compared |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 21.067549 | 21.057180 | 21.170037 | 14.024779 | -33.43% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.954827 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| a3_glm53_dc4k_b8:q1_b8_m8 | 47.113275 | — | — | — | not_established | 8 / 1 / 1 | auto / full |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 41.069081 | 39.690511 | 1.378570 | 3.36% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 33.619412 | 32.091259 | 1.528153 | 4.55% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 23.486220 | 22.012155 | 1.474066 | 6.28% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 28.226931 | 26.716230 | 1.510701 | 5.35% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 35.013734 | 33.489845 | 1.523889 | 4.35% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 37.826433 | 36.321708 | 1.504725 | 3.98% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 26.385455 | 24.884894 | 1.500561 | 5.69% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 43.281560 | 41.753200 | 1.528360 | 3.53% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 30.244200 | 28.749138 | 1.495061 | 4.94% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 35.070247 | 33.685758 | 1.384489 | 3.95% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 41.543810 | 40.003616 | 1.540195 | 3.71% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 44.811275 | 43.263086 | 1.548189 | 3.45% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 44.979779 | 43.458533 | 1.521246 | 3.38% | not_established | 16 / 1 / 16 | none / full |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.067549 | 20.805273 | 0.262276 | 1.24% | not_established | 8 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | dense_layer | 3 / 3 | 0.387506 | 0.384723 | 0.394250 | 0.352607 | -9.01% |
| a3_glm53_dc4k_b1:q1_b1_m1 | moe_layer | 54 / 75 | 0.503075 | 0.484378 | 0.566864 | 0.433536 | -13.82% |
| a3_glm53_dc4k_b8:q1_b8_m8 | dense_layer | 3 / 3 | 0.416038 | 0.413257 | 0.424403 | 0.364649 | -12.35% |
| a3_glm53_dc4k_b8:q1_b8_m8 | moe_layer | 75 / 75 | 0.610549 | 0.587718 | 0.698046 | 0.572750 | -6.19% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | dense_layer | 0 / 3 | 0.619493 | 0.429010 | 1.009248 | 0.705042 | +13.81% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | moe_layer | 11 / 42 | 0.932364 | 0.792325 | 1.381103 | 1.358595 | +45.72% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.128351 | -58.13% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 0 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.216976 | -38.27% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | dense_layer | 0 / 3 | 0.313856 | 0.240144 | 0.464978 | 0.147601 | -52.97% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | moe_layer | 0 / 42 | 0.479167 | 0.424416 | 0.634057 | 0.323380 | -32.51% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 57 / 78 | 0.498630 | 0.484310 | 0.566864 | 0.430423 | -13.68% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 78 / 78 | 0.603068 | 0.587228 | 0.698046 | 0.564746 | -6.35% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0 / 34 | 0.762836 | 0.772892 | 0.829536 | 1.252749 | +64.22% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 / 11 | 1.371034 | 1.377786 | 1.396007 | 1.507513 | +9.95% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.203222 | -32.49% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.235316 | -52.48% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0 / 34 | 0.412816 | 0.421465 | 0.428909 | 0.300369 | -27.24% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0 / 11 | 0.639166 | 0.633990 | 0.657478 | 0.346566 | -45.78% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 0.498630 | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 0.603068 | — | — |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 0.762836 | 0.735536 | 0.027300 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 1.371034 | 1.334754 | 0.036279 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0.412816 | 0.407564 | 0.005253 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0.639166 | 0.631647 | 0.007519 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | all | 77 | 5698 | 0.499986 | 0.484650 | 0.420279 | -13.28% |
| a3_glm53_dc4k_b1:q1_b1_m1 | mla | 77 | 5698 | 0.499986 | 0.484650 | 0.420279 | -13.28% |
| a3_glm53_dc4k_b8:q1_b8_m8 | all | 77 | 4697 | 0.605388 | 0.586108 | 0.558244 | -4.75% |
| a3_glm53_dc4k_b8:q1_b8_m8 | mla | 77 | 4697 | 0.605388 | 0.586108 | 0.558244 | -4.75% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | all | 44 | 1628 | 0.909285 | 0.788475 | 1.305753 | +65.60% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | kda | 33 | 1221 | 0.755369 | 0.773716 | 1.305753 | +68.76% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | mla | 11 | 407 | 1.371034 | 1.376707 | 1.507513 | +9.50% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.210468 | -30.09% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.210468 | -29.45% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.235316 | -52.00% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | all | 44 | 2332 | 0.468218 | 0.423968 | 0.315153 | -25.67% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 33 | 1749 | 0.411236 | 0.421213 | 0.315153 | -25.18% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 11 | 583 | 0.639166 | 0.633678 | 0.346566 | -45.31% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | 74 | 0.394250 | 0.385352 | 0.415732 | 0.352607 | -10.56% |
| a3_glm53_dc4k_b8:q1_b8_m8 | 61 | 0.424403 | 0.422672 | 0.425891 | 0.364649 | -14.08% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 37 | 1.009248 | 0.849777 | 0.965079 | 0.705042 | -30.14% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.128351 | -69.60% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 0.464978 | 0.474452 | 0.536593 | 0.147601 | -68.26% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | — | — | — | — |
| a3_glm53_dc4k_b8:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 8 | — | — | — | — |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 6 | 16 | 96 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | 6 | 6 | 36 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | 6 | 1 | 6 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | 6 | 3 | 18 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | 6 | 7 | 42 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | 6 | 10 | 60 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | 6 | 2 | 12 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | 6 | 14 | 84 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | 6 | 4 | 24 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | 6 | 8 | 48 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | 6 | 11 | 66 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | 6 | 12 | 72 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | 6 | 15 | 90 | unknown | 4096 | 16 | 51.552279 | 50.443027 | — | 46.524408 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 3 | — | 11.438829 | — | 9.752313 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_glm53_dc4k_b1:q1_b1_m1 | embedding | 74 | 0.007841 | 0.007839 | 0.007960 |
| a3_glm53_dc4k_b1:q1_b1_m1 | final_norm | 74 | 0.153796 | 0.153077 | 0.157037 |
| a3_glm53_dc4k_b1:q1_b1_m1 | lm_head | 74 | 0.216579 | 0.216606 | 0.217935 |
| a3_glm53_dc4k_b8:q1_b8_m8 | embedding | 61 | 0.003748 | 0.003760 | 0.003920 |
| a3_glm53_dc4k_b8:q1_b8_m8 | final_norm | 61 | 0.157658 | 0.157397 | 0.159617 |
| a3_glm53_dc4k_b8:q1_b8_m8 | lm_head | 61 | 0.272210 | 0.272394 | 0.273895 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | embedding | 37 | 0.008829 | 0.008820 | 0.009060 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | output_head_preparation | 37 | 0.007358 | 0.007360 | 0.007461 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | final_norm | 37 | 0.136148 | 0.135162 | 0.141542 |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | lm_head | 37 | 0.134106 | 0.133942 | 0.135363 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | embedding | 16 | 0.009413 | 0.009781 | 0.010120 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | output_head_preparation | 16 | 0.005665 | 0.005680 | 0.005820 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | final_norm | 16 | 0.140800 | 0.139463 | 0.145103 |
| glm53flash-a3-tp16-c16-livepre:q6_b6_m36 | lm_head | 16 | 0.118555 | 0.119532 | 0.122162 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | embedding | 13 | 0.003308 | 0.003280 | 0.003540 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | output_head_preparation | 13 | 0.004592 | 0.004580 | 0.004820 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | final_norm | 13 | 0.111430 | 0.110242 | 0.114462 |
| glm53flash-a3-tp16-c16-livepre:q6_b1_m6 | lm_head | 13 | 0.091983 | 0.092142 | 0.092762 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | embedding | 9 | 0.005600 | 0.005561 | 0.005980 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | output_head_preparation | 9 | 0.004851 | 0.004860 | 0.004980 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | final_norm | 9 | 0.130892 | 0.127222 | 0.152443 |
| glm53flash-a3-tp16-c16-livepre:q6_b3_m18 | lm_head | 9 | 0.115880 | 0.115882 | 0.117903 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | embedding | 7 | 0.006106 | 0.006080 | 0.006260 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | output_head_preparation | 7 | 0.005786 | 0.005780 | 0.005940 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | final_norm | 7 | 0.147500 | 0.141523 | 0.166983 |
| glm53flash-a3-tp16-c16-livepre:q6_b7_m42 | lm_head | 7 | 0.117742 | 0.118062 | 0.119462 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | embedding | 6 | 0.008247 | 0.008350 | 0.008440 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | output_head_preparation | 6 | 0.005980 | 0.006000 | 0.006120 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | final_norm | 6 | 0.132472 | 0.132692 | 0.133303 |
| glm53flash-a3-tp16-c16-livepre:q6_b10_m60 | lm_head | 6 | 0.125696 | 0.125943 | 0.126943 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | embedding | 5 | 0.004268 | 0.004281 | 0.004300 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | output_head_preparation | 5 | 0.004024 | 0.004080 | 0.004080 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | final_norm | 5 | 0.120771 | 0.119742 | 0.128023 |
| glm53flash-a3-tp16-c16-livepre:q6_b2_m12 | lm_head | 5 | 0.106558 | 0.106382 | 0.107562 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | embedding | 4 | 0.009325 | 0.009320 | 0.010880 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | output_head_preparation | 4 | 0.006905 | 0.006840 | 0.007120 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | final_norm | 4 | 0.134823 | 0.134732 | 0.135582 |
| glm53flash-a3-tp16-c16-livepre:q6_b14_m84 | lm_head | 4 | 0.128772 | 0.128682 | 0.130323 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | embedding | 4 | 0.006780 | 0.006680 | 0.007180 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | output_head_preparation | 4 | 0.004225 | 0.004280 | 0.004380 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | final_norm | 4 | 0.129198 | 0.128493 | 0.132643 |
| glm53flash-a3-tp16-c16-livepre:q6_b4_m24 | lm_head | 4 | 0.111252 | 0.111482 | 0.112162 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | embedding | 3 | 0.006673 | 0.006720 | 0.006720 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | output_head_preparation | 3 | 0.005847 | 0.005840 | 0.005920 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | final_norm | 3 | 0.137029 | 0.133223 | 0.145142 |
| glm53flash-a3-tp16-c16-livepre:q6_b8_m48 | lm_head | 3 | 0.121856 | 0.121482 | 0.122883 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | embedding | 2 | 0.009030 | 0.009030 | 0.009220 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | output_head_preparation | 2 | 0.007870 | 0.007870 | 0.008040 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | final_norm | 2 | 0.137733 | 0.137733 | 0.138843 |
| glm53flash-a3-tp16-c16-livepre:q6_b11_m66 | lm_head | 2 | 0.123722 | 0.123722 | 0.123742 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | embedding | 1 | 0.010040 | 0.010040 | 0.010040 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | output_head_preparation | 1 | 0.007760 | 0.007760 | 0.007760 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | final_norm | 1 | 0.137523 | 0.137523 | 0.137523 |
| glm53flash-a3-tp16-c16-livepre:q6_b12_m72 | lm_head | 1 | 0.125983 | 0.125983 | 0.125983 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | embedding | 1 | 0.008781 | 0.008781 | 0.008781 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | output_head_preparation | 1 | 0.007660 | 0.007660 | 0.007660 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | final_norm | 1 | 0.136902 | 0.136902 | 0.136902 |
| glm53flash-a3-tp16-c16-livepre:q6_b15_m90 | lm_head | 1 | 0.131863 | 0.131863 | 0.131863 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | embedding | 53 | 0.004169 | 0.004090 | 0.004625 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | output_head_preparation | 53 | 0.005233 | 0.005053 | 0.005939 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | final_norm | 53 | 0.036160 | 0.036119 | 0.036702 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | lm_head | 53 | 0.049451 | 0.049313 | 0.050247 |

Summary: {"case_count": 17, "compared_cases": 5, "failed_cases": 0, "measured_cases": 17, "passed_cases": 2, "source_case_count": 5, "unresolved_cases": 12}
