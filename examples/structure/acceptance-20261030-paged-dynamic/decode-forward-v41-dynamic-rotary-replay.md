# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "5251d0d5"}.

Variant: `v41-dynamic-rotary`. Baseline: null.

Sim 0.8.0; 252 package files; SHA256 `5dd1cb62f90c0f9651e18cd0931eb94c6a6be7b892b36ab3a6298a113a9f4270`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 14.929338 | 14.914454 | 14.928722 | 9.805704 | -34.32% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 18.624557 | 18.615864 | 18.640311 | 13.091327 | -29.71% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 13.238803 | 13.208635 | 13.227353 | 8.162892 | -38.34% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 13.134611 | 13.129265 | 13.145059 | 8.162892 | -37.85% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 13.291562 | 12.802981 | 12.816588 | 8.162892 | -38.59% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 26.328226 | 26.305803 | 26.335546 | 19.675251 | -25.27% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 27.285973 | 27.265820 | 27.290260 | 19.989387 | -26.74% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929338 | 14.831607 | 0.097731 | 0.65% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.624557 | 18.525544 | 0.099013 | 0.53% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.238803 | 13.143250 | 0.095554 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.134611 | 13.039066 | 0.095545 | 0.73% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.291562 | 13.195984 | 0.095578 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328226 | 26.228917 | 0.099309 | 0.38% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.285973 | 27.187901 | 0.098072 | 0.36% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | moe_layer | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.245143 | -34.31% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | moe_layer | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.327283 | -29.70% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | moe_layer | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.204072 | -38.33% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | moe_layer | 1 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.204072 | -37.84% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | moe_layer | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.204072 | -38.57% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | moe_layer | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.491881 | -25.26% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | moe_layer | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.499735 | -26.74% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 1 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.245143 | -34.31% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 1 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.327283 | -29.70% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.204072 | -38.33% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 1 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.204072 | -37.84% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 1 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.204072 | -38.57% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.491881 | -25.26% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.499735 | -26.74% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 0.373173 | 0.370790 | 0.002383 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 0.465552 | 0.463139 | 0.002414 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 0.330911 | 0.328581 | 0.002330 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 0.328305 | 0.325977 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 0.332229 | 0.329900 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 0.658143 | 0.655723 | 0.002420 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 0.682128 | 0.679698 | 0.002430 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | all | 39 | 5031 | 0.371581 | 0.352624 | 0.236010 | -33.07% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 39 | 5031 | 0.371581 | 0.352624 | 0.236010 | -33.07% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | all | 39 | 4095 | 0.463953 | 0.444058 | 0.318002 | -28.39% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 39 | 4095 | 0.463953 | 0.444058 | 0.318002 | -28.39% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | all | 39 | 5889 | 0.317677 | 0.300299 | 0.195014 | -35.06% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 39 | 5889 | 0.317677 | 0.300299 | 0.195014 | -35.06% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | all | 39 | 5928 | 0.315726 | 0.298357 | 0.195014 | -34.64% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 39 | 5928 | 0.315726 | 0.298357 | 0.195014 | -34.64% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | all | 39 | 5655 | 0.318949 | 0.301368 | 0.195014 | -35.29% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 39 | 5655 | 0.318949 | 0.301368 | 0.195014 | -35.29% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | all | 39 | 2925 | 0.655792 | 0.633369 | 0.482255 | -23.86% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 39 | 2925 | 0.655792 | 0.633369 | 0.482255 | -23.86% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | all | 39 | 2847 | 0.679042 | 0.654527 | 0.489290 | -25.25% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 39 | 2847 | 0.679042 | 0.654527 | 0.489290 | -25.25% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 0.435251 | 0.420089 | 0.424730 | 0.222504 | -48.88% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 0.527918 | 0.520862 | 0.527346 | 0.304496 | -42.32% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 0.847040 | 0.816238 | 0.820195 | 0.181508 | -78.57% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 0.818909 | 0.810300 | 0.814494 | 0.181508 | -77.84% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 0.850144 | 0.361077 | 0.365725 | 0.181508 | -78.65% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 0.749832 | 0.729175 | 0.734682 | 0.468749 | -37.49% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 0.802473 | 0.784160 | 0.791435 | 0.475784 | -40.71% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 1 | 2 | 2 | unknown | 2048 | 16 | 21.239293 | 20.616566 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 1 | 4 | 4 | unknown | 2048 | 32 | 22.363334 | 22.393036 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 4 | 16.557655 | 16.561941 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 1 | 15.041617 | 15.041617 | — | 12.786630 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 8 | 14.879684 | 14.880035 | — | 12.927205 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 1 | 8 | 8 | unknown | 2048 | 64 | 29.264897 | 28.942951 | — | 29.068484 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 1 | 16 | 16 | unknown | 2048 | 128 | — | 33.341304 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | embedding | 129 | 0.003381 | 0.003336 | 0.003618 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | output_head_preparation | 129 | 0.014962 | 0.014987 | 0.015300 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | final_norm | 129 | 0.002669 | 0.002646 | 0.002780 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | embedding | 105 | 0.004095 | 0.004051 | 0.004470 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | output_head_preparation | 105 | 0.016335 | 0.016280 | 0.016827 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | final_norm | 105 | 0.002770 | 0.002767 | 0.002848 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | output_head_preparation | 151 | 0.013937 | 0.013868 | 0.014536 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | final_norm | 151 | 0.002446 | 0.002420 | 0.002571 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | output_head_preparation | 152 | 0.014092 | 0.014053 | 0.014574 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | final_norm | 152 | 0.002451 | 0.002433 | 0.002556 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | embedding | 145 | 0.003245 | 0.003250 | 0.003357 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | output_head_preparation | 145 | 0.014064 | 0.014051 | 0.014507 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | final_norm | 145 | 0.002468 | 0.002439 | 0.002605 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | embedding | 75 | 0.003718 | 0.003682 | 0.003964 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | output_head_preparation | 75 | 0.018489 | 0.018470 | 0.019160 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | final_norm | 75 | 0.003217 | 0.003208 | 0.003327 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | embedding | 73 | 0.004227 | 0.004184 | 0.004651 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | output_head_preparation | 73 | 0.020123 | 0.020179 | 0.020740 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | final_norm | 73 | 0.003980 | 0.003950 | 0.004119 |

Summary: {"case_count": 7, "compared_cases": 7, "failed_cases": 0, "measured_cases": 7, "passed_cases": 0, "source_case_count": 7, "unresolved_cases": 0}
