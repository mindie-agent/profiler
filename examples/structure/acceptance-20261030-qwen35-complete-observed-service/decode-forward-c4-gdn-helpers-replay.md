# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "672a595fb1e102208d9fc904fad0ec9180fa437a"}.

Variant: `qwen35-c4-complete-GDN-helper-service-672a595f`. Baseline: {"path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-complete-observed-service/decode-forward-c4-batched-attention-replay.json", "sha256": "8b8aea7d1dbbb0e06151db3a220c8a64a82016f059eb051cc91411870b4da275", "size_bytes": 6649990}.

Sim 0.8.0; 283 package files; SHA256 `c347250c5f5e8aeccd0abda9d2a96a8e22928e2ed8668aed825671276f0e2ce5`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 11.551367 | 11.481642 | 11.817997 | 9.857738 | -14.66% | compared |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 6 | 8.746954 | 8.802646 | 8.838036 | — | — | unresolved: prediction_deferred_by_population_priority |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 1 | 9.699817 | 9.699817 | 9.699817 | — | — | unresolved: prediction_deferred_by_population_priority |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.551367 | 11.134754 | 0.416613 | 3.61% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 8.746954 | 8.336170 | 0.410784 | 4.70% | ACLGraph | 4 / 1 / 4 | none / full |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 9.699817 | 9.286883 | 0.412934 | 4.26% | ACLGraph | 4 / 1 / 4 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | moe_layer | 29 / 40 | 0.288763 | 0.283062 | 0.299996 | 0.246443 | -14.66% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 29 / 30 | 0.285398 | 0.282353 | 0.284296 | 0.247707 | -13.21% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0 / 10 | 0.298857 | 0.298829 | 0.301088 | 0.242653 | -18.81% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 0.285398 | 0.274983 | 0.010415 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 0.298857 | 0.288526 | 0.010332 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | all | 39 | 3276 | 0.286250 | 0.283215 | 0.247707 | -12.54% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gdn | 29 | 2436 | 0.281903 | 0.282722 | 0.247707 | -12.39% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | gqa | 10 | 840 | 0.298857 | 0.299161 | 0.242653 | -18.89% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 84 | 0.386758 | 0.297328 | 0.630548 | 0.247707 | -35.95% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 4 | 4 | 16 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | 4 | 1 | 4 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | 4 | 2 | 8 | unknown | 4096 | 4 | 7.155375 | 7.133439 | — | 5.955661 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | embedding | 84 | 0.003342 | 0.003354 | 0.003503 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | final_norm | 84 | 0.044109 | 0.044152 | 0.044444 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | lm_head | 84 | 0.075013 | 0.074908 | 0.076167 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | embedding | 6 | 0.002201 | 0.002262 | 0.002299 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | final_norm | 6 | 0.042644 | 0.042531 | 0.043062 |
| qwen35-35b-a5-tp4-c4-graph:q4_b1_m4 | lm_head | 6 | 0.072861 | 0.072813 | 0.073381 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | embedding | 1 | 0.002755 | 0.002755 | 0.002755 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | final_norm | 1 | 0.042579 | 0.042579 | 0.042579 |
| qwen35-35b-a5-tp4-c4-graph:q4_b2_m8 | lm_head | 1 | 0.072404 | 0.072404 | 0.072404 |

Summary: {"case_count": 3, "compared_cases": 1, "failed_cases": 0, "measured_cases": 3, "passed_cases": 1, "source_case_count": 1, "unresolved_cases": 2}
