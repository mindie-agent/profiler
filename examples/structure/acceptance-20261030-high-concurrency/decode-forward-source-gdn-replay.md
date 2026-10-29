# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "747c4f5f"}.

Variant: `source_gdn_control`. Baseline: {"interpretation": "Prior completed run retained unchanged; this control arm executes new source costs.", "path": "/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency/decode-forward-replay.json", "runtime_source_commit": "bc375e61", "sha256": "9b85505a1253d0ffb65eb3115f3dfc5a8c2bd5c85785420f7fbf6ba6820d6941"}.

Sim 0.8.0; 220 package files; SHA256 `660a5ae0042970232792885881fcdad6aa66cc169e527e3d0371c0c30dd25db2`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_qwen36_highconc_c40:q4_b40_m160 | 54 | 20.683911 | 20.611527 | 21.333773 | 14.378554 | -30.48% | compared |
| a5_qwen36_highconc_c128:q4_b128_m512 | 38 | 32.608990 | 32.227435 | 33.851394 | 25.455284 | -21.94% | compared |
| a5_qwen36_highconc_c4:q4_b4_m16 | 73 | 13.342454 | 13.244635 | 13.484726 | 7.842445 | -41.22% | compared |
| a5_qwen38_highconc_c32:q4_b32_m128 | 48 | 22.791335 | 22.711011 | 22.894013 | 15.190704 | -33.35% | compared |
| a5_qwen38_highconc_c128:q4_b128_m512 | 29 | 45.689314 | 45.690342 | 45.735162 | 38.166492 | -16.47% | compared |
| a5_qwen38_highconc_c4:q4_b4_m16 | 45 | 13.026721 | 13.005325 | 13.166872 | 7.548490 | -42.05% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_qwen36_highconc_c40:q4_b40_m160 | 20.683911 | 20.302463 | 0.381448 | 1.84% | FULL_AND_PIECEWISE | 8 / 1 / 1 | none / full |
| a5_qwen36_highconc_c128:q4_b128_m512 | 32.608990 | 32.315990 | 0.293001 | 0.90% | FULL_AND_PIECEWISE | 8 / 1 / 1 | none / full |
| a5_qwen36_highconc_c4:q4_b4_m16 | 13.342454 | 12.987191 | 0.355263 | 2.66% | FULL_AND_PIECEWISE | 8 / 1 / 1 | none / full |
| a5_qwen38_highconc_c32:q4_b32_m128 | 22.791335 | 22.352767 | 0.438568 | 1.92% | FULL_AND_PIECEWISE | 4 / 1 / 1 | none / full |
| a5_qwen38_highconc_c128:q4_b128_m512 | 45.689314 | 45.385279 | 0.304035 | 0.67% | FULL_AND_PIECEWISE | 4 / 1 / 1 | none / full |
| a5_qwen38_highconc_c4:q4_b4_m16 | 13.026721 | 12.555020 | 0.471701 | 3.62% | FULL_AND_PIECEWISE | 4 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | dense_layer | 0 / 64 | 0.322351 | 0.306924 | 0.310396 | 0.224665 | -30.30% |
| a5_qwen36_highconc_c128:q4_b128_m512 | dense_layer | 0 / 64 | 0.508731 | 0.499688 | 0.501555 | 0.397739 | -21.82% |
| a5_qwen36_highconc_c4:q4_b4_m16 | dense_layer | 0 / 64 | 0.207685 | 0.177630 | 0.182859 | 0.122538 | -41.00% |
| a5_qwen38_highconc_c32:q4_b32_m128 | dense_layer | 0 / 64 | 0.355259 | 0.378954 | 0.385319 | 0.237355 | -33.19% |
| a5_qwen38_highconc_c128:q4_b128_m512 | dense_layer | 48 / 64 | 0.713033 | 0.760891 | 0.763548 | 0.596351 | -16.36% |
| a5_qwen38_highconc_c4:q4_b4_m16 | dense_layer | 0 / 64 | 0.202655 | 0.207141 | 0.208962 | 0.117945 | -41.80% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | gdn | 0 / 48 | 0.333238 | 0.307781 | 0.311006 | 0.231965 | -30.39% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gqa | 0 / 16 | 0.289689 | 0.289770 | 0.290278 | 0.202764 | -30.01% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gdn | 0 / 48 | 0.515500 | 0.500258 | 0.502235 | 0.408048 | -20.84% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gqa | 0 / 16 | 0.488422 | 0.488369 | 0.490923 | 0.366813 | -24.90% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gdn | 0 / 48 | 0.215818 | 0.177193 | 0.178646 | 0.121909 | -43.51% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gqa | 0 / 16 | 0.183285 | 0.182644 | 0.183628 | 0.124426 | -32.11% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gdn | 0 / 48 | 0.381152 | 0.381610 | 0.385877 | 0.266743 | -30.02% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gqa | 0 / 16 | 0.277580 | 0.274090 | 0.275037 | 0.149191 | -46.25% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gdn | 48 / 48 | 0.761777 | 0.761850 | 0.763812 | 0.653825 | -14.17% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gqa | 0 / 16 | 0.566802 | 0.566580 | 0.568505 | 0.423929 | -25.21% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gdn | 0 / 48 | 0.207698 | 0.207635 | 0.209199 | 0.121072 | -41.71% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gqa | 0 / 16 | 0.187527 | 0.181657 | 0.181965 | 0.108565 | -42.11% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | gdn | 0.333238 | 0.328009 | 0.005229 |
| a5_qwen36_highconc_c40:q4_b40_m160 | gqa | 0.289689 | 0.284876 | 0.004813 |
| a5_qwen36_highconc_c128:q4_b128_m512 | gdn | 0.515500 | 0.511996 | 0.003504 |
| a5_qwen36_highconc_c128:q4_b128_m512 | gqa | 0.488422 | 0.483761 | 0.004662 |
| a5_qwen36_highconc_c4:q4_b4_m16 | gdn | 0.215818 | 0.211014 | 0.004804 |
| a5_qwen36_highconc_c4:q4_b4_m16 | gqa | 0.183285 | 0.178658 | 0.004627 |
| a5_qwen38_highconc_c32:q4_b32_m128 | gdn | 0.381152 | 0.375943 | 0.005209 |
| a5_qwen38_highconc_c32:q4_b32_m128 | gqa | 0.277580 | 0.269220 | 0.008360 |
| a5_qwen38_highconc_c128:q4_b128_m512 | gdn | 0.761777 | 0.758204 | 0.003573 |
| a5_qwen38_highconc_c128:q4_b128_m512 | gqa | 0.566802 | 0.561968 | 0.004834 |
| a5_qwen38_highconc_c4:q4_b4_m16 | gdn | 0.207698 | 0.202701 | 0.004997 |
| a5_qwen38_highconc_c4:q4_b4_m16 | gqa | 0.187527 | 0.176586 | 0.010941 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | all | 63 | 3402 | 0.302907 | 0.306570 | 0.231965 | -24.34% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gdn | 47 | 2538 | 0.307407 | 0.307554 | 0.231965 | -24.58% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gqa | 16 | 864 | 0.289689 | 0.289637 | 0.202764 | -29.99% |
| a5_qwen36_highconc_c128:q4_b128_m512 | all | 63 | 2394 | 0.497137 | 0.499606 | 0.408048 | -18.33% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gdn | 47 | 1786 | 0.500103 | 0.500082 | 0.408048 | -18.40% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gqa | 16 | 608 | 0.488422 | 0.488279 | 0.366813 | -24.88% |
| a5_qwen36_highconc_c4:q4_b4_m16 | all | 63 | 4599 | 0.178748 | 0.177573 | 0.121909 | -31.35% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gdn | 47 | 3431 | 0.177203 | 0.177050 | 0.121909 | -31.14% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gqa | 16 | 1168 | 0.183285 | 0.182605 | 0.124426 | -31.86% |
| a5_qwen38_highconc_c32:q4_b32_m128 | all | 63 | 3024 | 0.354520 | 0.378495 | 0.266743 | -29.53% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gdn | 47 | 2256 | 0.380712 | 0.381320 | 0.266743 | -30.05% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gqa | 16 | 768 | 0.277580 | 0.273753 | 0.149191 | -45.50% |
| a5_qwen38_highconc_c128:q4_b128_m512 | all | 63 | 1827 | 0.712261 | 0.760662 | 0.653825 | -14.05% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gdn | 47 | 1363 | 0.761779 | 0.761792 | 0.653825 | -14.17% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gqa | 16 | 464 | 0.566802 | 0.566466 | 0.423929 | -25.16% |
| a5_qwen38_highconc_c4:q4_b4_m16 | all | 63 | 2835 | 0.202386 | 0.207114 | 0.121072 | -41.54% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gdn | 47 | 2115 | 0.207444 | 0.207576 | 0.121072 | -41.67% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gqa | 16 | 720 | 0.187527 | 0.181647 | 0.108565 | -40.23% |

### Exact pooled steady layer calls

This separate population uses the integer span of every aligned layer invocation except Layer 0. It provides an actual pooled P50; Sim repeats each matching layer prediction once per Forward. Full body timing above is unchanged.

| Case | Attention group | Layers | Layer calls | Real pooled mean ms | Real pooled P50 ms | Real pooled P90 ms | Sim pooled P50 ms | P50 error |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | all | 63 | 3402 | 0.302907 | 0.306140 | 0.310989 | 0.231965 | -24.23% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gdn | 47 | 2538 | 0.307407 | 0.307661 | 0.311620 | 0.231965 | -24.60% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gqa | 16 | 864 | 0.289689 | 0.289581 | 0.293898 | 0.202764 | -29.98% |
| a5_qwen36_highconc_c128:q4_b128_m512 | all | 63 | 2394 | 0.497137 | 0.499061 | 0.502971 | 0.408048 | -18.24% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gdn | 47 | 1786 | 0.500103 | 0.499981 | 0.503442 | 0.408048 | -18.39% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gqa | 16 | 608 | 0.488422 | 0.488665 | 0.497603 | 0.366813 | -24.94% |
| a5_qwen36_highconc_c4:q4_b4_m16 | all | 63 | 4599 | 0.178748 | 0.177736 | 0.183002 | 0.121909 | -31.41% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gdn | 47 | 3431 | 0.177203 | 0.177161 | 0.178893 | 0.121909 | -31.19% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gqa | 16 | 1168 | 0.183285 | 0.182612 | 0.184428 | 0.124426 | -31.86% |
| a5_qwen38_highconc_c32:q4_b32_m128 | all | 63 | 3024 | 0.354520 | 0.378269 | 0.385695 | 0.266743 | -29.48% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gdn | 47 | 2256 | 0.380712 | 0.381312 | 0.386192 | 0.266743 | -30.05% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gqa | 16 | 768 | 0.277580 | 0.273906 | 0.278252 | 0.149191 | -45.53% |
| a5_qwen38_highconc_c128:q4_b128_m512 | all | 63 | 1827 | 0.712261 | 0.760410 | 0.765089 | 0.653825 | -14.02% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gdn | 47 | 1363 | 0.761779 | 0.761669 | 0.765542 | 0.653825 | -14.16% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gqa | 16 | 464 | 0.566802 | 0.566473 | 0.572280 | 0.423929 | -25.16% |
| a5_qwen38_highconc_c4:q4_b4_m16 | all | 63 | 2835 | 0.202386 | 0.206745 | 0.209578 | 0.121072 | -41.44% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gdn | 47 | 2115 | 0.207444 | 0.207490 | 0.209706 | 0.121072 | -41.65% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gqa | 16 | 720 | 0.187527 | 0.181596 | 0.183678 | 0.108565 | -40.22% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | 54 | 1.547308 | 1.469181 | 2.171547 | 0.231965 | -85.01% |
| a5_qwen36_highconc_c128:q4_b128_m512 | 38 | 1.239153 | 0.798407 | 2.424613 | 0.408048 | -67.07% |
| a5_qwen36_highconc_c4:q4_b4_m16 | 73 | 2.030701 | 1.931990 | 2.164814 | 0.121909 | -94.00% |
| a5_qwen38_highconc_c32:q4_b32_m128 | 48 | 0.401811 | 0.375551 | 0.379297 | 0.266743 | -33.61% |
| a5_qwen38_highconc_c128:q4_b128_m512 | 29 | 0.761688 | 0.761920 | 0.766392 | 0.653825 | -14.16% |
| a5_qwen38_highconc_c4:q4_b4_m16 | 45 | 0.219625 | 0.219669 | 0.221519 | 0.121072 | -44.87% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | 4 | 40 | 4104 | 40 | 12.839582 | 12.870617 | 13.698161 | 10.137586 |
| a5_qwen36_highconc_c128:q4_b128_m512 | 4 | 128 | 4104 | 128 | 17.645612 | 17.500859 | 20.464879 | 14.023292 |
| a5_qwen36_highconc_c4:q4_b4_m16 | 4 | 4 | 4104 | 4 | 8.059150 | 8.041687 | 10.003893 | 6.381290 |
| a5_qwen38_highconc_c32:q4_b32_m128 | 4 | 32 | 4104 | 32 | 14.101780 | 14.106413 | 15.903896 | 10.367068 |
| a5_qwen38_highconc_c128:q4_b128_m512 | 4 | 128 | 4104 | 128 | 27.946485 | 27.887855 | 28.320504 | 24.995237 |
| a5_qwen38_highconc_c4:q4_b4_m16 | 4 | 4 | 4104 | 4 | 11.137499 | 11.048730 | 16.458697 | 8.196429 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | embedding | 54 | 0.004765 | 0.004703 | 0.005322 |
| a5_qwen36_highconc_c40:q4_b40_m160 | final_norm | 54 | 0.037118 | 0.037024 | 0.037973 |
| a5_qwen36_highconc_c40:q4_b40_m160 | lm_head | 54 | 0.178405 | 0.178379 | 0.179324 |
| a5_qwen36_highconc_c128:q4_b128_m512 | embedding | 38 | 0.006034 | 0.005968 | 0.006681 |
| a5_qwen36_highconc_c128:q4_b128_m512 | final_norm | 38 | 0.041093 | 0.041087 | 0.041763 |
| a5_qwen36_highconc_c128:q4_b128_m512 | lm_head | 38 | 0.402881 | 0.402783 | 0.403390 |
| a5_qwen36_highconc_c4:q4_b4_m16 | embedding | 73 | 0.003597 | 0.003623 | 0.003802 |
| a5_qwen36_highconc_c4:q4_b4_m16 | final_norm | 73 | 0.032247 | 0.032223 | 0.032516 |
| a5_qwen36_highconc_c4:q4_b4_m16 | lm_head | 73 | 0.097013 | 0.096930 | 0.097982 |
| a5_qwen38_highconc_c32:q4_b32_m128 | embedding | 48 | 0.004640 | 0.004575 | 0.005413 |
| a5_qwen38_highconc_c32:q4_b32_m128 | final_norm | 48 | 0.037252 | 0.037282 | 0.037908 |
| a5_qwen38_highconc_c32:q4_b32_m128 | lm_head | 48 | 0.229199 | 0.229154 | 0.230429 |
| a5_qwen38_highconc_c128:q4_b128_m512 | embedding | 29 | 0.005760 | 0.005688 | 0.006661 |
| a5_qwen38_highconc_c128:q4_b128_m512 | final_norm | 29 | 0.042436 | 0.042390 | 0.043485 |
| a5_qwen38_highconc_c128:q4_b128_m512 | lm_head | 29 | 0.772040 | 0.771808 | 0.772096 |
| a5_qwen38_highconc_c4:q4_b4_m16 | embedding | 45 | 0.003569 | 0.003569 | 0.003972 |
| a5_qwen38_highconc_c4:q4_b4_m16 | final_norm | 45 | 0.033019 | 0.032977 | 0.033359 |
| a5_qwen38_highconc_c4:q4_b4_m16 | lm_head | 45 | 0.193530 | 0.193411 | 0.194871 |

Summary: {"case_count": 6, "compared_cases": 6, "failed_cases": 0, "measured_cases": 6, "passed_cases": 0, "source_case_count": 6, "unresolved_cases": 0}
