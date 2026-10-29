# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "09811dad268203b6d021e01715b1c245d877c40f"}.

Sim 0.8.0; 228 package files; SHA256 `57d40b5b746923be0f725879f83825c3d4e428230ab72fa9bf920c0fde5d3360`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 13.134611 | 13.129265 | 13.145059 | 8.200338 | -37.57% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 13.291562 | 12.802981 | 12.816588 | 8.200338 | -38.30% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 26.328226 | 26.305803 | 26.335546 | 18.284700 | -30.55% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.134611 | 13.039066 | 0.095545 | 0.73% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.291562 | 13.195984 | 0.095578 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328226 | 26.228917 | 0.099309 | 0.38% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | moe_layer | 1 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.205008 | -37.56% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | moe_layer | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.205008 | -38.29% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | moe_layer | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.457117 | -30.54% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 1 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.205008 | -37.56% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.205008 | -38.29% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.457117 | -30.54% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 0.328305 | 0.325977 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 0.332229 | 0.329900 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 0.658143 | 0.655723 | 0.002420 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | all | 39 | 5928 | 0.315726 | 0.298357 | 0.195475 | -34.48% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 39 | 5928 | 0.315726 | 0.298357 | 0.195475 | -34.48% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | all | 39 | 5655 | 0.318949 | 0.301368 | 0.195475 | -35.14% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 39 | 5655 | 0.318949 | 0.301368 | 0.195475 | -35.14% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | all | 39 | 2925 | 0.655792 | 0.633369 | 0.447068 | -29.41% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 39 | 2925 | 0.655792 | 0.633369 | 0.447068 | -29.41% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 0.818909 | 0.810300 | 0.814494 | 0.195475 | -76.13% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 0.850144 | 0.361077 | 0.365725 | 0.195475 | -77.01% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 0.749832 | 0.729175 | 0.734682 | 0.447068 | -40.38% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 1 | 15.041617 | 15.041617 | — | 12.786630 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 8 | 14.879684 | 14.880035 | — | 12.927205 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 1 | 8 | 8 | unknown | 2048 | 64 | 29.264897 | 28.942951 | — | 29.068484 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | output_head_preparation | 152 | 0.014092 | 0.014053 | 0.014574 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | final_norm | 152 | 0.002451 | 0.002433 | 0.002556 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | embedding | 145 | 0.003245 | 0.003250 | 0.003357 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | output_head_preparation | 145 | 0.014064 | 0.014051 | 0.014507 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | final_norm | 145 | 0.002468 | 0.002439 | 0.002605 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | embedding | 75 | 0.003718 | 0.003682 | 0.003964 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | output_head_preparation | 75 | 0.018489 | 0.018470 | 0.019160 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | final_norm | 75 | 0.003217 | 0.003208 | 0.003327 |

Summary: {"case_count": 3, "compared_cases": 3, "failed_cases": 0, "measured_cases": 3, "passed_cases": 0, "source_case_count": 3, "unresolved_cases": 0}
