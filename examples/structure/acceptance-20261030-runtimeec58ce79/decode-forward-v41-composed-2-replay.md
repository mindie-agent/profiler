# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "ec58ce7921583967a50e803c78b962d90f8273b0"}.

Variant: `body-runtimeec58ce79-v41-composed`. Baseline: null.

Sim 0.8.0; 265 package files; SHA256 `4c161acd03117dde23616de2e49eec94468d09cdd640d77497044caf0cc0e57b`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 26.328226 | 26.305803 | 26.335546 | 18.932524 | -28.09% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 13.238803 | 13.208635 | 13.227353 | 7.430228 | -43.88% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328226 | 26.228917 | 0.099309 | 0.38% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.238803 | 13.143250 | 0.095554 | 0.72% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | moe_layer | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.473313 | -28.08% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | moe_layer | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.185756 | -43.87% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 1 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.473313 | -28.08% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 1 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.185756 | -43.87% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 0.658143 | 0.655723 | 0.002420 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 0.330911 | 0.328581 | 0.002330 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | all | 39 | 2925 | 0.655792 | 0.633369 | 0.463687 | -26.79% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 39 | 2925 | 0.655792 | 0.633369 | 0.463687 | -26.79% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | all | 39 | 5889 | 0.317677 | 0.300299 | 0.176697 | -41.16% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 39 | 5889 | 0.317677 | 0.300299 | 0.176697 | -41.16% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 0.749832 | 0.729175 | 0.734682 | 0.450181 | -39.96% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 0.847040 | 0.816238 | 0.820195 | 0.163191 | -80.73% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 1 | 8 | 8 | unknown | 2048 | 64 | 29.264897 | 28.942951 | — | 29.068484 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 4 | 16.557655 | 16.561941 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | embedding | 75 | 0.003718 | 0.003682 | 0.003964 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | output_head_preparation | 75 | 0.018489 | 0.018470 | 0.019160 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | final_norm | 75 | 0.003217 | 0.003208 | 0.003327 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | output_head_preparation | 151 | 0.013937 | 0.013868 | 0.014536 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | final_norm | 151 | 0.002446 | 0.002420 | 0.002571 |

Summary: {"case_count": 2, "compared_cases": 2, "failed_cases": 0, "measured_cases": 2, "passed_cases": 0, "source_case_count": 2, "unresolved_cases": 0}
