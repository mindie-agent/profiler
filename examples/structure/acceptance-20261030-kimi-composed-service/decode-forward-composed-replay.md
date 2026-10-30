# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "3b72ea2d"}.

Variant: `composed-source-service-3b72ea2d`. Baseline: null.

Sim 0.8.0; 276 package files; SHA256 `57520ed725bfe6358585bd404f4cefa1f7702c00aabbc9294fecfb44a2f21db8`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 42.155614 | -5.62% | compared |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 36.968860 | -7.62% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666193 | 43.970836 | 0.695357 | 1.56% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.018728 | 39.322926 | 0.695802 | 1.74% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 0 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.251978 | -30.39% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 91 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.455358 | -5.44% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 0 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.251978 | -25.43% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 91 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.398980 | -7.49% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.390131 | -5.70% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 23 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.634411 | -5.53% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.390131 | -5.54% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 23 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.418296 | -12.83% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0.413723 | 0.407971 | 0.005752 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0.671523 | 0.659202 | 0.012321 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0.413032 | 0.407278 | 0.005754 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0.479865 | 0.467530 | 0.012334 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.396014 | -4.77% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.391832 | -5.40% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.634298 | -4.53% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.396014 | -4.65% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.391832 | -5.36% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.418184 | -11.44% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.251978 | -30.39% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.251978 | -25.43% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 1 | 32 | 32 | unknown | 16392 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 1 | 32 | 32 | unknown | 4104 | 32 | — | — | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | embedding | 41 | 0.003452 | 0.003466 | 0.003683 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | final_norm | 41 | 0.005865 | 0.005876 | 0.006045 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | lm_head | 41 | 0.117608 | 0.117655 | 0.118201 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | embedding | 46 | 0.003423 | 0.003405 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | final_norm | 46 | 0.005558 | 0.005548 | 0.005768 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | lm_head | 46 | 0.117594 | 0.117492 | 0.118427 |

Summary: {"case_count": 2, "compared_cases": 2, "failed_cases": 0, "measured_cases": 2, "passed_cases": 2, "source_case_count": 2, "unresolved_cases": 0}
