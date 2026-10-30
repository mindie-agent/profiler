# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "2f48346b"}.

Variant: `observable-service-2f48346b`. Baseline: null.

Sim 0.8.0; 276 package files; SHA256 `e71d76a0e8fb32f59648503ffa653c55a08cf912e081941a4af9c62e61905a24`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 41.995725 | +4.94% | compared |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 47.218681 | +5.71% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 26.328226 | 26.305803 | 26.335546 | 24.811578 | -5.76% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 27.285973 | 27.265820 | 27.290260 | 25.539779 | -6.40% | compared |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 39.247386 | 39.244948 | 39.262920 | 40.763839 | +3.86% | compared |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 36.985292 | 36.952793 | 36.968819 | 38.387860 | +3.79% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 14.929338 | 14.914454 | 14.928722 | 13.748800 | -7.91% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 18.624557 | 18.615864 | 18.640311 | 17.361229 | -6.78% | compared |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 13.238803 | 13.208635 | 13.227353 | 12.549524 | -5.21% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 13.291562 | 12.802981 | 12.816588 | 12.155047 | -8.55% | compared |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 13.134611 | 13.129265 | 13.145059 | 12.436061 | -5.32% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.018728 | 39.322926 | 0.695802 | 1.74% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666193 | 43.970836 | 0.695357 | 1.56% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328226 | 26.228917 | 0.099309 | 0.38% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.285973 | 27.187901 | 0.098072 | 0.36% | not_established | 1 / 8 / 8 | auto / full |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247386 | 38.566577 | 0.680809 | 1.73% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985292 | 36.304665 | 0.680627 | 1.84% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929338 | 14.831607 | 0.097731 | 0.65% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.624557 | 18.525544 | 0.099013 | 0.53% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.238803 | 13.143250 | 0.095554 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.291562 | 13.195984 | 0.095578 | 0.72% | not_established | 1 / 8 / 8 | auto / full |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.134611 | 13.039066 | 0.095545 | 0.73% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 1 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.323614 | -4.23% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 91 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.452810 | +4.99% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 1 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.324476 | -10.37% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 91 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.509572 | +5.82% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | moe_layer | 38 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.620289 | -5.75% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | moe_layer | 38 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.638494 | -6.40% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | dense_layer | 1 / 1 | 0.304707 | 0.304707 | 0.304707 | 0.287712 | -5.58% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | moe_layer | 91 / 92 | 0.423260 | 0.387824 | 0.524838 | 0.439815 | +3.91% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | dense_layer | 1 / 1 | 0.335331 | 0.335331 | 0.335331 | 0.287202 | -14.35% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | moe_layer | 91 / 92 | 0.398339 | 0.387665 | 0.429149 | 0.413995 | +3.93% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | moe_layer | 31 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.343720 | -7.89% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | moe_layer | 35 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.434031 | -6.77% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | moe_layer | 37 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.313738 | -5.19% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | moe_layer | 34 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.303876 | -8.53% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | moe_layer | 37 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.310902 | -5.30% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 69 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.449353 | +8.79% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 23 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.457364 | -4.69% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 69 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.450263 | +8.83% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 23 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.672371 | +0.13% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 38 / 40 | 0.658143 | 0.633750 | 0.745193 | 0.620289 | -5.75% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 38 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.638494 | -6.40% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 69 / 69 | 0.384646 | 0.385628 | 0.391398 | 0.412555 | +7.26% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 23 / 24 | 0.529336 | 0.522407 | 0.529076 | 0.511850 | -3.30% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 69 / 69 | 0.385013 | 0.385311 | 0.391916 | 0.412212 | +7.06% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 23 / 24 | 0.434026 | 0.426707 | 0.433591 | 0.413839 | -4.65% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 31 / 40 | 0.373173 | 0.352684 | 0.435251 | 0.343720 | -7.89% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 35 / 40 | 0.465552 | 0.444202 | 0.534740 | 0.434031 | -6.77% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 37 / 40 | 0.330911 | 0.300274 | 0.378501 | 0.313738 | -5.19% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 34 / 40 | 0.332229 | 0.301635 | 0.381292 | 0.303876 | -8.53% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 37 / 40 | 0.328305 | 0.298647 | 0.379531 | 0.310902 | -5.30% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0.413032 | 0.407278 | 0.005754 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0.479865 | 0.467530 | 0.012334 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0.413723 | 0.407971 | 0.005752 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0.671523 | 0.659202 | 0.012321 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 0.658143 | 0.655723 | 0.002420 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 0.682128 | 0.679698 | 0.002430 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0.384646 | 0.379054 | 0.005591 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0.529336 | 0.517159 | 0.012177 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0.385013 | 0.379424 | 0.005589 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0.434026 | 0.421850 | 0.012176 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 0.373173 | 0.370790 | 0.002383 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 0.465552 | 0.463139 | 0.002414 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 0.330911 | 0.328581 | 0.002330 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 0.332229 | 0.329900 | 0.002329 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 0.328305 | 0.325977 | 0.002329 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.451202 | +8.64% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.451202 | +8.98% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.456889 | -3.25% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.452113 | +8.72% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.452113 | +9.15% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.671896 | +1.13% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | all | 39 | 2925 | 0.655792 | 0.633369 | 0.608413 | -3.94% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | mla | 39 | 2925 | 0.655792 | 0.633369 | 0.608413 | -3.94% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | all | 39 | 2847 | 0.679042 | 0.654527 | 0.626159 | -4.33% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 39 | 2847 | 0.679042 | 0.654527 | 0.626159 | -4.33% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | all | 92 | 4324 | 0.423260 | 0.387808 | 0.414386 | +6.85% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 68 | 3196 | 0.385821 | 0.385597 | 0.414386 | +7.47% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 24 | 1128 | 0.529336 | 0.522342 | 0.511375 | -2.10% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | all | 92 | 4508 | 0.398339 | 0.387570 | 0.414047 | +6.83% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 68 | 3332 | 0.385744 | 0.385530 | 0.414047 | +7.40% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 24 | 1176 | 0.434026 | 0.426871 | 0.413367 | -3.16% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | all | 39 | 5031 | 0.371581 | 0.352624 | 0.332538 | -5.70% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | mla | 39 | 5031 | 0.371581 | 0.352624 | 0.332538 | -5.70% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | all | 39 | 4095 | 0.463953 | 0.444058 | 0.422743 | -4.80% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | mla | 39 | 4095 | 0.463953 | 0.444058 | 0.422743 | -4.80% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | all | 39 | 5889 | 0.317677 | 0.300299 | 0.302535 | +0.74% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | mla | 39 | 5889 | 0.317677 | 0.300299 | 0.302535 | +0.74% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | all | 39 | 5655 | 0.318949 | 0.301368 | 0.293019 | -2.77% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | mla | 39 | 5655 | 0.318949 | 0.301368 | 0.293019 | -2.77% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | all | 39 | 5928 | 0.315726 | 0.298357 | 0.299667 | +0.44% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | mla | 39 | 5928 | 0.315726 | 0.298357 | 0.299667 | +0.44% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.323614 | -4.23% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.324476 | -10.37% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 75 | 0.749832 | 0.729175 | 0.734682 | 0.590525 | -21.25% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 0.802473 | 0.784160 | 0.791435 | 0.610068 | -23.98% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 0.304707 | 0.302280 | 0.304417 | 0.287712 | -5.58% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 0.335331 | 0.302283 | 0.304588 | 0.287202 | -14.35% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 129 | 0.435251 | 0.420089 | 0.424730 | 0.313881 | -27.89% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 105 | 0.527918 | 0.520862 | 0.527346 | 0.404771 | -23.33% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 151 | 0.847040 | 0.816238 | 0.820195 | 0.290409 | -65.71% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 145 | 0.850144 | 0.361077 | 0.365725 | 0.274887 | -67.67% |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 152 | 0.818909 | 0.810300 | 0.814494 | 0.287820 | -64.85% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 1 | 32 | 32 | unknown | 4104 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 1 | 32 | 32 | unknown | 16392 | 32 | — | — | — | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 1 | 8 | 8 | unknown | 2048 | 64 | 29.264897 | 28.942951 | — | 29.068484 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 1 | 16 | 16 | unknown | 2048 | 128 | — | 33.341304 | — | — |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 1 | 16 | 16 | unknown | 16392 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 1 | 16 | 16 | unknown | 4104 | 16 | — | — | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 1 | 2 | 2 | unknown | 2048 | 16 | 21.239293 | 20.616566 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 1 | 4 | 4 | unknown | 2048 | 32 | 22.363334 | 22.393036 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 4 | 16.557655 | 16.561941 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 8 | 14.879684 | 14.880035 | — | 12.927205 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 2048 | 1 | 15.041617 | 15.041617 | — | 12.786630 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | embedding | 46 | 0.003423 | 0.003405 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | final_norm | 46 | 0.005558 | 0.005548 | 0.005768 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | lm_head | 46 | 0.117594 | 0.117492 | 0.118427 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | embedding | 41 | 0.003452 | 0.003466 | 0.003683 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | final_norm | 41 | 0.005865 | 0.005876 | 0.006045 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | lm_head | 41 | 0.117608 | 0.117655 | 0.118201 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | embedding | 75 | 0.003718 | 0.003682 | 0.003964 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | output_head_preparation | 75 | 0.018489 | 0.018470 | 0.019160 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | final_norm | 75 | 0.003217 | 0.003208 | 0.003327 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | embedding | 73 | 0.004227 | 0.004184 | 0.004651 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | output_head_preparation | 73 | 0.020123 | 0.020179 | 0.020740 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | final_norm | 73 | 0.003980 | 0.003950 | 0.004119 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | embedding | 47 | 0.004621 | 0.004452 | 0.005158 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | final_norm | 47 | 0.004149 | 0.004128 | 0.004346 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | lm_head | 47 | 0.092373 | 0.092297 | 0.093138 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | embedding | 49 | 0.004593 | 0.004509 | 0.005168 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | final_norm | 49 | 0.004091 | 0.004082 | 0.004295 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | lm_head | 49 | 0.092424 | 0.092431 | 0.093127 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | embedding | 129 | 0.003381 | 0.003336 | 0.003618 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | output_head_preparation | 129 | 0.014962 | 0.014987 | 0.015300 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | final_norm | 129 | 0.002669 | 0.002646 | 0.002780 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | embedding | 105 | 0.004095 | 0.004051 | 0.004470 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | output_head_preparation | 105 | 0.016335 | 0.016280 | 0.016827 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | final_norm | 105 | 0.002770 | 0.002767 | 0.002848 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | output_head_preparation | 151 | 0.013937 | 0.013868 | 0.014536 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | final_norm | 151 | 0.002446 | 0.002420 | 0.002571 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | embedding | 145 | 0.003245 | 0.003250 | 0.003357 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | output_head_preparation | 145 | 0.014064 | 0.014051 | 0.014507 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | final_norm | 145 | 0.002468 | 0.002439 | 0.002605 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | output_head_preparation | 152 | 0.014092 | 0.014053 | 0.014574 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | final_norm | 152 | 0.002451 | 0.002433 | 0.002556 |

Summary: {"case_count": 11, "compared_cases": 11, "failed_cases": 0, "measured_cases": 11, "passed_cases": 11, "source_case_count": 11, "unresolved_cases": 0}
