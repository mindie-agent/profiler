# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "40e4300ea7ccc1123759f6201cc2d69e3aa77ad6"}.

Variant: `body-runtime40e4300e-qwen-hccl`. Baseline: null.

Sim 0.8.0; 271 package files; SHA256 `ab51c56356b3b6f11a130dd7a59d2fd894b99148d0917fc4cc40189102286124`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| qwen36-a5-tp2-c12:q4_b12_m48 | 55 | 24.225774 | 24.052762 | 24.710750 | 18.849871 | -22.19% | compared |
| qwen36-a5-tp2-c96:q4_b96_m384 | 24 | 63.853365 | 63.561524 | 65.419347 | 53.947109 | -15.51% | compared |
| qwen36-a5-tp2-c1:q4_b1_m4 | 85 | 12.318284 | 12.279117 | 12.362065 | 7.726466 | -37.28% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| qwen36-a5-tp2-c12:q4_b12_m48 | 24.225774 | 23.857914 | 0.367860 | 1.52% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |
| qwen36-a5-tp2-c96:q4_b96_m384 | 63.853365 | 63.564919 | 0.288446 | 0.45% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |
| qwen36-a5-tp2-c1:q4_b1_m4 | 12.318284 | 11.955626 | 0.362658 | 2.94% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | dense_layer | 0 / 64 | 0.377769 | 0.402171 | 0.410517 | 0.294529 | -22.03% |
| qwen36-a5-tp2-c96:q4_b96_m384 | dense_layer | 16 / 64 | 0.996962 | 1.057504 | 1.060586 | 0.842924 | -15.45% |
| qwen36-a5-tp2-c1:q4_b1_m4 | dense_layer | 0 / 64 | 0.191663 | 0.191309 | 0.193238 | 0.120726 | -37.01% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 0 / 48 | 0.408829 | 0.404015 | 0.411737 | 0.320555 | -21.59% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 0 / 16 | 0.284588 | 0.284472 | 0.285798 | 0.216453 | -23.94% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 0 / 48 | 1.064900 | 1.058731 | 1.060743 | 0.894095 | -16.04% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 16 / 16 | 0.793149 | 0.792915 | 0.794736 | 0.689408 | -13.08% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 0 / 48 | 0.192884 | 0.191633 | 0.193801 | 0.121575 | -36.97% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 0 / 16 | 0.188000 | 0.188164 | 0.188947 | 0.118180 | -37.14% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 0.408829 | 0.403692 | 0.005137 |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 0.284588 | 0.280043 | 0.004545 |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 1.064900 | 1.061406 | 0.003494 |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 0.793149 | 0.788590 | 0.004559 |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 0.192884 | 0.188024 | 0.004860 |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 0.188000 | 0.183155 | 0.004844 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | all | 63 | 3465 | 0.373974 | 0.401967 | 0.320555 | -20.25% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gdn | 47 | 2585 | 0.404404 | 0.403298 | 0.320555 | -20.52% |
| qwen36-a5-tp2-c12:q4_b12_m48 | gqa | 16 | 880 | 0.284588 | 0.284266 | 0.216453 | -23.86% |
| qwen36-a5-tp2-c96:q4_b96_m384 | all | 63 | 1512 | 0.991056 | 1.057303 | 0.894095 | -15.44% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gdn | 47 | 1128 | 1.058428 | 1.058404 | 0.894095 | -15.52% |
| qwen36-a5-tp2-c96:q4_b96_m384 | gqa | 16 | 384 | 0.793149 | 0.792751 | 0.689408 | -13.04% |
| qwen36-a5-tp2-c1:q4_b1_m4 | all | 63 | 5355 | 0.190897 | 0.191201 | 0.121575 | -36.42% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gdn | 47 | 3995 | 0.191883 | 0.191473 | 0.121575 | -36.51% |
| qwen36-a5-tp2-c1:q4_b1_m4 | gqa | 16 | 1360 | 0.188000 | 0.187574 | 0.118180 | -37.00% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | 55 | 0.616826 | 0.393097 | 1.098361 | 0.320555 | -48.03% |
| qwen36-a5-tp2-c96:q4_b96_m384 | 24 | 1.369095 | 1.068151 | 2.946417 | 0.894095 | -34.69% |
| qwen36-a5-tp2-c1:q4_b1_m4 | 85 | 0.239954 | 0.198388 | 0.228723 | 0.121575 | -49.33% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | 4 | 12 | 48 | unknown | 4104 | 12 | 12.737826 | 12.657177 | 13.606740 | 10.182462 |
| qwen36-a5-tp2-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | 31.633699 | 31.824432 | 30.608581 | 30.201530 |
| qwen36-a5-tp2-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | 8.043380 | 8.043380 | 8.239878 | 5.939812 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| qwen36-a5-tp2-c12:q4_b12_m48 | embedding | 55 | 0.004170 | 0.004186 | 0.004651 |
| qwen36-a5-tp2-c12:q4_b12_m48 | final_norm | 55 | 0.036794 | 0.036682 | 0.037460 |
| qwen36-a5-tp2-c12:q4_b12_m48 | lm_head | 55 | 0.402777 | 0.402984 | 0.405412 |
| qwen36-a5-tp2-c96:q4_b96_m384 | embedding | 24 | 0.005769 | 0.005723 | 0.006566 |
| qwen36-a5-tp2-c96:q4_b96_m384 | final_norm | 24 | 0.040660 | 0.040637 | 0.041410 |
| qwen36-a5-tp2-c96:q4_b96_m384 | lm_head | 24 | 1.198757 | 1.198186 | 1.198974 |
| qwen36-a5-tp2-c1:q4_b1_m4 | embedding | 85 | 0.003458 | 0.003498 | 0.003705 |
| qwen36-a5-tp2-c1:q4_b1_m4 | final_norm | 85 | 0.031253 | 0.031243 | 0.031619 |
| qwen36-a5-tp2-c1:q4_b1_m4 | lm_head | 85 | 0.376379 | 0.376409 | 0.378443 |

Summary: {"case_count": 3, "compared_cases": 3, "failed_cases": 0, "measured_cases": 3, "passed_cases": 0, "source_case_count": 3, "unresolved_cases": 0}
