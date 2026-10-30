# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "21c30821d87a757bace8cf6b2fffea2536db643e"}.

Variant: `q397-highconc-native-21c30821`. Baseline: null.

Sim 0.8.0; 288 package files; SHA256 `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 76.089008 | 76.132320 | 76.632160 | 67.050948 | -11.88% | compared |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 119.054350 | 119.130970 | 119.486280 | 113.556975 | -4.62% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 76.089008 | 75.005135 | 1.083873 | 1.42% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 119.054350 | 118.048221 | 1.006129 | 0.85% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | moe_layer | 48 / 60 | 1.266992 | 1.278787 | 1.381181 | 1.117516 | -11.80% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | moe_layer | 60 / 60 | 1.983005 | 1.996372 | 2.053669 | 1.892616 | -4.56% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 41 / 45 | 1.235511 | 1.203183 | 1.311698 | 1.115200 | -9.74% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 7 / 15 | 1.361434 | 1.341377 | 1.455367 | 1.124465 | -17.41% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 45 / 45 | 1.959216 | 1.940194 | 2.025587 | 1.911369 | -2.44% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 / 15 | 2.054372 | 2.022060 | 2.122093 | 1.836358 | -10.61% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 1.235511 | 1.218935 | 0.016576 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 1.361434 | 1.343537 | 0.017897 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 1.959216 | 1.944578 | 0.014638 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 2.054372 | 2.036149 | 0.018223 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | all | 59 | 1357 | 1.265579 | 1.271900 | 1.115200 | -12.32% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 44 | 1012 | 1.232902 | 1.207710 | 1.115200 | -7.66% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 15 | 345 | 1.361434 | 1.346900 | 1.124465 | -16.51% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | all | 59 | 1062 | 1.981915 | 1.992890 | 1.911369 | -4.09% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 44 | 792 | 1.957214 | 1.935175 | 1.911369 | -1.23% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 | 270 | 2.054372 | 2.031370 | 1.836358 | -9.60% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 1.350335 | 1.286500 | 1.407580 | 1.115200 | -17.41% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 2.047277 | 1.998270 | 2.165240 | 1.911369 | -6.64% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 48 | 39.264375 | 39.367968 | — | — |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 4 | 160 | 640 | unknown | 4104 | 136 | 59.413752 | 59.082504 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | embedding | 23 | 0.010090 | 0.010000 | 0.010280 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | final_norm | 23 | 0.166548 | 0.166700 | 0.168400 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | lm_head | 23 | 0.272729 | 0.272680 | 0.274060 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | embedding | 18 | 0.011200 | 0.011080 | 0.011840 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | final_norm | 18 | 0.188559 | 0.189710 | 0.192900 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | lm_head | 18 | 0.435398 | 0.436110 | 0.441320 |

Summary: {"case_count": 2, "compared_cases": 2, "failed_cases": 0, "measured_cases": 2, "passed_cases": 2, "source_case_count": 2, "unresolved_cases": 0}
