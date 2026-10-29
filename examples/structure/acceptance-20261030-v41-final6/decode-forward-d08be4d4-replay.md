# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "d08be4d4a4370da6df6503d815f781a8a647e510"}.

Variant: `source-bound-v41-final6-current-defaults`. Baseline: {"basis": "source-declared generic target body; native fused MC2/FlashComm/DSpark and MQSMLA coverage limitations remain explicit"}.

Sim 0.8.0; 233 package files; SHA256 `f097037ac70c2db602f15ddc9cf4fe7ac5a8a428dd0dc11de3500c6361f20f1f`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 49.984739 | 49.802195 | 50.230116 | 52.407548 | +4.85% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 20 | 50.227508 | 50.207347 | 50.437972 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 15 | 34.239103 | 33.682167 | 36.061940 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 8 | 48.703795 | 48.703717 | 49.026360 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 1 | 185.130761 | 185.130761 | 185.130761 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 54.967136 | 54.880343 | 55.046901 | 55.855149 | +1.62% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 17 | 50.515059 | 50.459912 | 50.932142 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 16 | 51.750107 | 51.719686 | 52.027841 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 14 | 51.592999 | 33.731086 | 38.400113 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 4 | 50.042250 | 49.960392 | 50.329354 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 3 | 51.607722 | 50.563670 | 54.167837 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 1 | 262.496916 | 262.496916 | 262.496916 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 47.654000 | 47.425103 | 47.666347 | 50.240465 | +5.43% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 30 | 50.154700 | 34.835994 | 37.649748 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 61.811249 | 61.628568 | 62.041601 | 63.335847 | +2.47% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 13 | 72.359330 | 33.725246 | 173.014883 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 11 | 59.510906 | 59.510991 | 59.770166 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 8 | 55.144861 | 55.133909 | 55.338375 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 7 | 63.460852 | 58.535011 | 92.715408 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 5 | 54.821604 | 54.715706 | 55.163818 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 4 | 58.827980 | 58.789946 | 59.143718 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 2 | 56.627079 | 56.627079 | 56.742766 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 2 | 49.513901 | 49.513901 | 50.934043 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 2 | 57.975442 | 57.975442 | 58.051780 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 1 | 50.256336 | 50.256336 | 50.256336 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 48.581862 | 48.411553 | 48.662328 | 51.618320 | +6.25% | compared |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 28 | 52.940304 | 48.199387 | 48.363454 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 16 | 48.606206 | 33.771646 | 34.877383 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 4 | 47.116268 | 47.165278 | 47.201657 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 27.285973 | 27.265820 | 27.290260 | 19.508241 | -28.50% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 49.984739 | 49.317682 | 0.667058 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 50.227508 | 49.552575 | 0.674933 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 34.239103 | 33.579092 | 0.660011 | 1.93% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 48.703795 | 48.003864 | 0.699931 | 1.44% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 185.130761 | 181.542159 | 3.588602 | 1.94% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 54.967136 | 54.296272 | 0.670864 | 1.22% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 50.515059 | 49.845037 | 0.670022 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 51.750107 | 51.077579 | 0.672528 | 1.30% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 51.592999 | 50.678830 | 0.914169 | 1.77% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 50.042250 | 49.369207 | 0.673044 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 51.607722 | 50.920601 | 0.687121 | 1.33% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 262.496916 | 259.635735 | 2.861181 | 1.09% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 47.654000 | 46.948644 | 0.705356 | 1.48% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 50.154700 | 48.252669 | 1.902031 | 3.79% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 61.811249 | 61.114951 | 0.696298 | 1.13% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 72.359330 | 70.911770 | 1.447560 | 2.00% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 59.510906 | 58.818469 | 0.692436 | 1.16% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 55.144861 | 54.462681 | 0.682180 | 1.24% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 63.460852 | 62.707830 | 0.753022 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 54.821604 | 54.149919 | 0.671686 | 1.23% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 58.827980 | 58.125277 | 0.702703 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 56.627079 | 55.953760 | 0.673318 | 1.19% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 49.513901 | 48.795326 | 0.718575 | 1.45% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 57.975442 | 57.304422 | 0.671019 | 1.16% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 50.256336 | 49.584132 | 0.672204 | 1.34% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 48.581862 | 47.882945 | 0.698917 | 1.44% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 52.940304 | 52.210892 | 0.729412 | 1.38% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 48.606206 | 47.850255 | 0.755951 | 1.56% | not_established | 4 / 4 / 16 | eager / full |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 47.116268 | 46.410050 | 0.706218 | 1.50% | not_established | 4 / 4 / 16 | eager / full |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.285973 | 27.187901 | 0.098072 | 0.36% | not_established | 1 / 8 / 8 | auto / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | moe_layer | 40 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.310189 | +4.25% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | moe_layer | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.396379 | +1.21% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | moe_layer | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.256012 | +4.78% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | moe_layer | 40 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.583396 | +2.14% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | moe_layer | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.290458 | +5.64% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | moe_layer | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.487706 | -28.50% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 40 / 40 | 1.256829 | 1.189883 | 1.439809 | 1.310189 | +4.25% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 / 40 | 1.379618 | 1.308635 | 1.584825 | 1.396379 | +1.21% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 / 40 | 1.198705 | 1.131824 | 1.351136 | 1.256012 | +4.78% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 40 / 40 | 1.550226 | 1.465994 | 1.871356 | 1.583396 | +2.14% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 40 / 40 | 1.221524 | 1.164096 | 1.419689 | 1.290458 | +5.64% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 1 / 40 | 0.682128 | 0.654867 | 0.771288 | 0.487706 | -28.50% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 1.256829 | 1.240894 | 0.015936 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 1.379618 | 1.363695 | 0.015922 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 1.198705 | 1.181799 | 0.016906 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 1.550226 | 1.533748 | 0.016479 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 1.221524 | 1.204788 | 0.016735 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 0.682128 | 0.679698 | 0.002430 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | all | 39 | 1248 | 1.252138 | 1.188276 | 1.291320 | +8.67% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | mla | 39 | 1248 | 1.252138 | 1.188276 | 1.291320 | +8.67% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | all | 39 | 858 | 1.371480 | 1.307714 | 1.373580 | +5.04% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | mla | 39 | 858 | 1.371480 | 1.307714 | 1.373580 | +5.04% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | all | 39 | 1872 | 1.179467 | 1.129198 | 1.239989 | +9.81% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | mla | 39 | 1872 | 1.179467 | 1.129198 | 1.239989 | +9.81% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | all | 39 | 819 | 1.547673 | 1.462711 | 1.552448 | +6.13% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | mla | 39 | 819 | 1.547673 | 1.462711 | 1.552448 | +6.13% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | all | 39 | 1131 | 1.216364 | 1.158637 | 1.272571 | +9.83% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | mla | 39 | 1131 | 1.216364 | 1.158637 | 1.272571 | +9.83% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | all | 39 | 2847 | 0.679042 | 0.654527 | 0.476840 | -27.15% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | mla | 39 | 2847 | 0.679042 | 0.654527 | 0.476840 | -27.15% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 32 | 1.439809 | 1.298684 | 1.648967 | 1.291320 | -10.31% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 22 | 1.697000 | 1.564018 | 1.749065 | 1.373580 | -19.06% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 48 | 1.948982 | 1.656527 | 2.027239 | 1.239989 | -36.38% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 21 | 1.649789 | 1.473370 | 1.851743 | 1.552448 | -5.90% |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 29 | 1.422735 | 1.252335 | 1.455071 | 1.272571 | -10.55% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 73 | 0.802473 | 0.784160 | 0.791435 | 0.476840 | -40.58% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | 8 | 6 | 48 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | 8 | 4 | 32 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 16 | — | 58.612550 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | 8 | 9 | 72 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | 8 | 7 | 56 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | 8 | 8 | 64 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | 8 | 6 | 48 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 32 | — | 64.090632 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | 8 | 2 | 16 | unknown | 4096 | 4 | — | 56.226793 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 4 | — | 56.226793 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | 8 | 17 | 136 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | 8 | 15 | 120 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | 8 | 10 | 80 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | 8 | 16 | 128 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | 8 | 9 | 72 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | 8 | 14 | 112 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | 8 | 12 | 96 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | 8 | 13 | 104 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | 8 | 5 | 40 | unknown | 4096 | 64 | — | 81.775784 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | 8 | 4 | 32 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | 8 | 3 | 24 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | 8 | 1 | 8 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | 8 | 2 | 16 | unknown | 4096 | 8 | — | 57.909682 | — | — |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 1 | 16 | 16 | unknown | 2048 | 128 | — | 33.341304 | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | embedding | 32 | 0.008862 | 0.008890 | 0.009200 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | output_head_preparation | 32 | 0.356277 | 0.355973 | 0.358613 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b5_m40 | final_norm | 32 | 0.014816 | 0.014760 | 0.015240 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | embedding | 20 | 0.007475 | 0.007430 | 0.007759 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | output_head_preparation | 20 | 0.351240 | 0.351013 | 0.352973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b6_m48 | final_norm | 20 | 0.009730 | 0.009729 | 0.009960 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | output_head_preparation | 15 | 0.312376 | 0.311674 | 0.315154 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | final_norm | 15 | 0.005845 | 0.005820 | 0.006080 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b1_m8 | embedding | 2 | 0.003830 | 0.003830 | 0.004060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | embedding | 8 | 0.005952 | 0.005970 | 0.007260 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | output_head_preparation | 8 | 0.333853 | 0.334693 | 0.336334 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b4_m32 | final_norm | 8 | 0.011817 | 0.011810 | 0.012420 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | embedding | 1 | 0.005840 | 0.005840 | 0.005840 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | output_head_preparation | 1 | 0.350973 | 0.350973 | 0.350973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16:q8_b3_m24 | final_norm | 1 | 0.009360 | 0.009360 | 0.009360 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | embedding | 22 | 0.007214 | 0.007140 | 0.007660 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | output_head_preparation | 22 | 0.368570 | 0.367993 | 0.370632 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b9_m72 | final_norm | 22 | 0.014659 | 0.014680 | 0.014880 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | embedding | 17 | 0.006761 | 0.006940 | 0.007120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | output_head_preparation | 17 | 0.358314 | 0.358513 | 0.360813 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b7_m56 | final_norm | 17 | 0.011328 | 0.011260 | 0.011700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | embedding | 16 | 0.006899 | 0.006860 | 0.007060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | output_head_preparation | 16 | 0.359054 | 0.359463 | 0.361693 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b8_m64 | final_norm | 16 | 0.013194 | 0.013189 | 0.013640 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | output_head_preparation | 14 | 0.313637 | 0.313224 | 0.315394 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b1_m8 | final_norm | 14 | 0.005784 | 0.005830 | 0.006019 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | embedding | 4 | 0.007105 | 0.006370 | 0.009480 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | output_head_preparation | 4 | 0.353663 | 0.353323 | 0.357252 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b6_m48 | final_norm | 4 | 0.009695 | 0.009620 | 0.009940 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | embedding | 3 | 0.006387 | 0.006040 | 0.007280 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | output_head_preparation | 3 | 0.354926 | 0.355413 | 0.356253 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b5_m40 | final_norm | 3 | 0.014506 | 0.014540 | 0.014620 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | embedding | 1 | 0.005700 | 0.005700 | 0.005700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | output_head_preparation | 1 | 0.378372 | 0.378372 | 0.378372 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32:q8_b3_m24 | final_norm | 1 | 0.008400 | 0.008400 | 0.008400 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | output_head_preparation | 48 | 0.325974 | 0.324164 | 0.332453 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | final_norm | 48 | 0.007295 | 0.007260 | 0.007680 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b2_m16 | embedding | 17 | 0.004945 | 0.004900 | 0.005120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | output_head_preparation | 30 | 0.351012 | 0.312613 | 0.316094 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | final_norm | 30 | 0.005851 | 0.005840 | 0.006120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4:q8_b1_m8 | embedding | 11 | 0.003611 | 0.003620 | 0.003780 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | embedding | 21 | 0.008124 | 0.008119 | 0.008460 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | output_head_preparation | 21 | 0.402302 | 0.402352 | 0.406091 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b17_m136 | final_norm | 21 | 0.015404 | 0.015340 | 0.015859 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | output_head_preparation | 13 | 0.317838 | 0.312053 | 0.326034 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | final_norm | 13 | 0.005801 | 0.005760 | 0.006040 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b1_m8 | embedding | 1 | 0.003740 | 0.003740 | 0.003740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | embedding | 11 | 0.007723 | 0.007740 | 0.008440 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | output_head_preparation | 11 | 0.385694 | 0.385952 | 0.387272 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b15_m120 | final_norm | 11 | 0.017636 | 0.017440 | 0.018120 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | embedding | 8 | 0.007963 | 0.008340 | 0.008600 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | output_head_preparation | 8 | 0.370152 | 0.370113 | 0.372393 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b10_m80 | final_norm | 8 | 0.016395 | 0.016379 | 0.016740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | embedding | 7 | 0.008251 | 0.008080 | 0.009140 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | output_head_preparation | 7 | 0.394901 | 0.392072 | 0.413811 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b16_m128 | final_norm | 7 | 0.014714 | 0.014700 | 0.015180 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | embedding | 5 | 0.007140 | 0.007340 | 0.007700 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | output_head_preparation | 5 | 0.369109 | 0.370793 | 0.371773 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b9_m72 | final_norm | 5 | 0.014908 | 0.015000 | 0.015060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | embedding | 4 | 0.008470 | 0.008430 | 0.008880 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | output_head_preparation | 4 | 0.388932 | 0.389422 | 0.392272 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b14_m112 | final_norm | 4 | 0.021625 | 0.021700 | 0.022040 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | embedding | 2 | 0.008250 | 0.008250 | 0.008300 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | output_head_preparation | 2 | 0.384402 | 0.384402 | 0.385072 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b12_m96 | final_norm | 2 | 0.013640 | 0.013640 | 0.013740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | output_head_preparation | 2 | 0.325094 | 0.325094 | 0.326253 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b3_m24 | final_norm | 2 | 0.008959 | 0.008959 | 0.009099 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | embedding | 2 | 0.007120 | 0.007120 | 0.007220 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | output_head_preparation | 2 | 0.377993 | 0.377993 | 0.379273 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b13_m104 | final_norm | 2 | 0.015480 | 0.015480 | 0.015879 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | embedding | 1 | 0.008560 | 0.008560 | 0.008560 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | output_head_preparation | 1 | 0.359973 | 0.359973 | 0.359973 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64:q8_b5_m40 | final_norm | 1 | 0.015000 | 0.015000 | 0.015000 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | embedding | 29 | 0.007257 | 0.007240 | 0.007380 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | output_head_preparation | 29 | 0.336221 | 0.336313 | 0.338114 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b4_m32 | final_norm | 29 | 0.011816 | 0.011760 | 0.012219 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | embedding | 28 | 0.003791 | 0.003720 | 0.004000 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | output_head_preparation | 28 | 0.327837 | 0.326354 | 0.329513 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b3_m24 | final_norm | 28 | 0.008859 | 0.008840 | 0.009080 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | output_head_preparation | 16 | 0.312757 | 0.312584 | 0.314913 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | final_norm | 16 | 0.005796 | 0.005780 | 0.006019 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b1_m8 | embedding | 2 | 0.003660 | 0.003660 | 0.003740 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | embedding | 4 | 0.003770 | 0.003680 | 0.004060 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | output_head_preparation | 4 | 0.325269 | 0.325554 | 0.327473 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8:q8_b2_m16 | final_norm | 4 | 0.007425 | 0.007380 | 0.007620 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | embedding | 73 | 0.004227 | 0.004184 | 0.004651 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | output_head_preparation | 73 | 0.020123 | 0.020179 | 0.020740 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | final_norm | 73 | 0.003980 | 0.003950 | 0.004119 |

Summary: {"case_count": 30, "compared_cases": 6, "failed_cases": 0, "measured_cases": 30, "passed_cases": 5, "source_case_count": 6, "unresolved_cases": 24}
