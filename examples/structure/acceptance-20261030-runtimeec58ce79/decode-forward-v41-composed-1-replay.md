# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "ec58ce7921583967a50e803c78b962d90f8273b0"}.

Variant: `body-runtimeec58ce79-v41-composed`. Baseline: null.

Sim 0.8.0; 265 package files; SHA256 `4c161acd03117dde23616de2e49eec94468d09cdd640d77497044caf0cc0e57b`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 13.291562 | 12.802981 | 12.816588 | 7.430228 | -44.10% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 18.624557 | 18.615864 | 18.640311 | 12.360845 | -33.63% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.291562 | 13.195984 | 0.095578 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.624557 | 18.525544 | 0.099013 | 0.53% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | moe_layer | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.185756 | -44.09% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | moe_layer | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.309021 | -33.62% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.185756 | -44.09% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.309021 | -33.62% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 0.332229 | 0.329900 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 0.465552 | 0.463139 | 0.002414 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | all | 39 | 5655 | 0.318949 | 0.301368 | 0.176697 | -41.37% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 39 | 5655 | 0.318949 | 0.301368 | 0.176697 | -41.37% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | all | 39 | 4095 | 0.463953 | 0.444058 | 0.299740 | -32.50% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 39 | 4095 | 0.463953 | 0.444058 | 0.299740 | -32.50% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 0.850144 | 0.361077 | 0.365725 | 0.163191 | -80.80% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 0.527918 | 0.520862 | 0.527346 | 0.286234 | -45.78% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 8 | 14.879684 | 14.880035 | — | 12.927205 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 1 | 4 | 4 | unknown | 2048 | 32 | 22.363334 | 22.393036 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | embedding | 145 | 0.003245 | 0.003250 | 0.003357 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | output_head_preparation | 145 | 0.014064 | 0.014051 | 0.014507 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | final_norm | 145 | 0.002468 | 0.002439 | 0.002605 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | embedding | 105 | 0.004095 | 0.004051 | 0.004470 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | output_head_preparation | 105 | 0.016335 | 0.016280 | 0.016827 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | final_norm | 105 | 0.002770 | 0.002767 | 0.002848 |

Summary: {"case_count": 2, "compared_cases": 2, "failed_cases": 0, "measured_cases": 2, "passed_cases": 0, "source_case_count": 2, "unresolved_cases": 0}
