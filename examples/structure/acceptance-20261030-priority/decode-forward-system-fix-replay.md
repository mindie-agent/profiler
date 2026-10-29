# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "1f5b2971"}.

Variant: `system_workload_fix_1f5b2971`. Baseline: {"path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-priority/decode-forward-second-wave-replay.json", "runtime_source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec", "selection_basis": "same captured q/B populations; Qwen397 aggregate-expert cases and GLM batch-scaling endpoints"}.

Sim 0.8.0; 225 package files; SHA256 `0b82bdf55fb758dbb2560586b32b7bc88ea951da8f97e1bc8d869c94dd6c2a62`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 76.089008 | 76.132320 | 76.632160 | 84.849228 | +11.51% | compared |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 119.054350 | 119.130970 | 119.486280 | 137.372823 | +15.39% | compared |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 32.555493 | 32.533125 | 32.673798 | 54.183640 | +66.43% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 76.089008 | 75.005135 | 1.083873 | 1.42% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 119.054350 | 118.048221 | 1.006129 | 0.85% | FULL_DECODE_ONLY | 16 / 1 / 1 | none / full |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.555493 | — | — | — | FULL_DECODE_ONLY | 8 / 4 / 32 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | moe_layer | 34 / 60 | 1.266992 | 1.278787 | 1.381181 | 1.414154 | +11.62% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | moe_layer | 22 / 60 | 1.983005 | 1.996372 | 2.053669 | 2.289547 | +15.46% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.257923 | 0.257923 | 0.257923 | 0.185040 | -28.26% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | moe_layer | 1 / 92 | 0.351316 | 0.341372 | 0.378042 | 0.586787 | +67.03% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 26 / 45 | 1.235511 | 1.203183 | 1.311698 | 1.379846 | +11.68% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 8 / 15 | 1.361434 | 1.341377 | 1.455367 | 1.517078 | +11.43% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 22 / 45 | 1.959216 | 1.940194 | 2.025587 | 2.237721 | +14.22% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 0 / 15 | 2.054372 | 2.022060 | 2.122093 | 2.445025 | +19.02% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0 / 69 | 0.338761 | 0.339556 | 0.344976 | 0.584448 | +72.53% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 1 / 24 | 0.383520 | 0.376471 | 0.383168 | 0.576773 | +50.39% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 1.235511 | 1.218935 | 0.016576 |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 1.361434 | 1.343537 | 0.017897 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 1.959216 | 1.944578 | 0.014638 |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 2.054372 | 2.036149 | 0.018223 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0.338761 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 0.383520 | — | — |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | all | 59 | 1357 | 1.265579 | 1.271900 | 1.379846 | +8.49% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gdn | 44 | 1012 | 1.232902 | 1.207710 | 1.379846 | +14.25% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | gqa | 15 | 345 | 1.361434 | 1.346900 | 1.517078 | +12.63% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | all | 59 | 1062 | 1.981915 | 1.992890 | 2.237721 | +12.29% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gdn | 44 | 792 | 1.957214 | 1.935175 | 2.237721 | +15.63% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | gqa | 15 | 270 | 2.054372 | 2.031370 | 2.445025 | +20.36% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | all | 92 | 5796 | 0.351316 | 0.340746 | 0.590160 | +73.20% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 68 | 4284 | 0.339949 | 0.338622 | 0.590160 | +74.28% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 24 | 1512 | 0.383520 | 0.374659 | 0.576571 | +53.89% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 23 | 1.350335 | 1.286500 | 1.407580 | 1.379846 | +2.19% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 18 | 2.047277 | 1.998270 | 2.165240 | 2.237721 | +9.30% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 0.257923 | 0.238298 | 0.250875 | 0.185040 | -28.26% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 48 | 39.264375 | 39.367968 | — | — |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 4 | 160 | 640 | unknown | 4104 | 136 | 59.413752 | 59.082504 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 32768 | 1 | 66.586585 | 66.586585 | — | 64.353701 |

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
| a5_kimi_k3_p32768_c1:q1_b1_m1 | embedding | 63 | 0.003108 | 0.003075 | 0.003299 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | final_norm | 63 | 0.004363 | 0.004258 | 0.004465 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | lm_head | 63 | 0.092173 | 0.092155 | 0.092665 |

Summary: {"case_count": 3, "compared_cases": 3, "failed_cases": 0, "measured_cases": 3, "passed_cases": 1, "source_case_count": 3, "unresolved_cases": 0}
