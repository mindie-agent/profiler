# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "c2261d63"}.

Variant: `runtime-c226-timeout-retry`. Baseline: null.

Sim 0.8.0; 243 package files; SHA256 `80be1bb5d6e2bfe5f69fd6b1ac1119a335799550d114a90f4d4237ecb4983844`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| glm53flash-a5-tp8-c96:q4_b96_m384 | 27 | 57.589679 | 57.572611 | 57.734379 | — | — | failed: body_prediction_timeout |
| qwen36-a5-tp2-c96:q4_b96_m384 | 24 | 63.853365 | 63.561524 | 65.419347 | — | — | failed: body_prediction_timeout |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.589679 | 57.354872 | 0.234807 | 0.41% | not_established | 8 / 1 / 1 | none / full |
| qwen36-a5-tp2-c96:q4_b96_m384 | 63.853365 | 63.564919 | 0.288446 | 0.45% | ACLGraph; campaign report | 2 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| glm53flash-a5-tp8-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | — | 26.457978 | — | 27.999716 |
| qwen36-a5-tp2-c96:q4_b96_m384 | 4 | 96 | 384 | unknown | 4104 | 96 | 31.633699 | 31.824432 | 30.608581 | 30.201530 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| glm53flash-a5-tp8-c96:q4_b96_m384 | embedding | 27 | 0.005289 | 0.005236 | 0.006251 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | output_head_preparation | 27 | 0.011084 | 0.010990 | 0.011458 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | final_norm | 27 | 0.042626 | 0.042703 | 0.043037 |
| glm53flash-a5-tp8-c96:q4_b96_m384 | lm_head | 27 | 0.160268 | 0.160208 | 0.160486 |
| qwen36-a5-tp2-c96:q4_b96_m384 | embedding | 24 | 0.005769 | 0.005723 | 0.006566 |
| qwen36-a5-tp2-c96:q4_b96_m384 | final_norm | 24 | 0.040660 | 0.040637 | 0.041410 |
| qwen36-a5-tp2-c96:q4_b96_m384 | lm_head | 24 | 1.198757 | 1.198186 | 1.198974 |

Summary: {"case_count": 2, "compared_cases": 0, "failed_cases": 2, "measured_cases": 2, "passed_cases": 0, "source_case_count": 2, "unresolved_cases": 0}
