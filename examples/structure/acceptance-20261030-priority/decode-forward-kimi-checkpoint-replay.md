# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "d9118c6e71ed9c75362c06fc7063be4ab97317ec"}.

Variant: `kimi_current_checkpoint_reference_conditional`. Baseline: {"case_id": "a5_kimi_k3_p32768_c1:q1_b1_m1", "path": "/Users/maoxx241/code/profiler/examples/structure/acceptance-20261030-priority/decode-forward-priority-replay.json"}.

Sim 0.8.0; 221 package files; SHA256 `5d7c051180a936039cadc42d39e1d3e7a993d652b322c105b16219de135d5ac6`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 32.555493 | 32.533125 | 32.673798 | 46.902452 | +44.07% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.555493 | — | — | — | FULL_DECODE_ONLY | 8 / 4 / 32 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.257923 | 0.257923 | 0.257923 | 0.176693 | -31.49% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | moe_layer | 1 / 92 | 0.351316 | 0.341372 | 0.378042 | 0.507889 | +44.57% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0 / 69 | 0.338761 | 0.339556 | 0.344976 | 0.506065 | +49.39% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 1 / 24 | 0.383520 | 0.376471 | 0.383168 | 0.499332 | +30.20% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 0.338761 | — | — |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 0.383520 | — | — |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | all | 92 | 5796 | 0.351316 | 0.340746 | 0.510753 | +49.89% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | kda | 68 | 4284 | 0.339949 | 0.338622 | 0.510753 | +50.83% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | mla | 24 | 1512 | 0.383520 | 0.374659 | 0.499138 | +33.22% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 63 | 0.257923 | 0.238298 | 0.250875 | 0.176693 | -31.49% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 32768 | 1 | 66.586585 | 66.586585 | — | 64.353701 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_kimi_k3_p32768_c1:q1_b1_m1 | embedding | 63 | 0.003108 | 0.003075 | 0.003299 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | final_norm | 63 | 0.004363 | 0.004258 | 0.004465 |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | lm_head | 63 | 0.092173 | 0.092155 | 0.092665 |

Summary: {"case_count": 1, "compared_cases": 1, "failed_cases": 0, "measured_cases": 1, "passed_cases": 0, "source_case_count": 1, "unresolved_cases": 0}
