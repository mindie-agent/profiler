# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "672a595fb1e102208d9fc904fad0ec9180fa437a"}.

Variant: `observed-norm-quant-post-672a595f`. Baseline: null.

Sim 0.8.0; 283 package files; SHA256 `c347250c5f5e8aeccd0abda9d2a96a8e22928e2ed8668aed825671276f0e2ce5`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 46.528233 | 46.498735 | 46.644535 | 47.071528 | +1.17% | compared |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 37.668964 | 37.665316 | 37.761150 | 35.167461 | -6.64% | compared |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 2 | 37.705175 | 37.705175 | 37.843605 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 2 | 37.467978 | 37.467978 | 38.254596 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 1 | 38.396873 | 38.396873 | 38.396873 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 1 | 38.002127 | 38.002127 | 38.002127 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 35 | 38.713189 | 38.721850 | 38.759233 | 36.207062 | -6.47% | compared |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 1 | 38.635279 | 38.635279 | 38.635279 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 30 | 33.030918 | 33.026482 | 33.164019 | 29.627802 | -10.30% | compared |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 4 | 18.010107 | 17.896268 | 18.412903 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 3 | 15.697300 | 15.704795 | 15.723134 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 2 | 24.984322 | 24.984322 | 25.001368 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 1 | 33.211164 | 33.211164 | 33.211164 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 1 | 32.232000 | 32.232000 | 32.232000 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 1 | 31.922655 | 31.922655 | 31.922655 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 1 | 21.416720 | 21.416720 | 21.416720 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 32 | 33.616091 | 33.625860 | 33.709694 | 30.209746 | -10.13% | compared |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 2 | 29.255343 | 29.255343 | 29.307106 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 2 | 21.440818 | 21.440818 | 21.440852 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 2 | 15.623967 | 15.623967 | 15.655241 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 1 | 33.357579 | 33.357579 | 33.357579 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 1 | 32.536283 | 32.536283 | 32.536283 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 1 | 24.989969 | 24.989969 | 24.989969 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 1 | 17.717363 | 17.717363 | 17.717363 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 28.833324 | 28.828410 | 28.884507 | 25.431005 | -11.80% | compared |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 3 | 25.112799 | 25.067088 | 25.282855 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 2 | 21.340235 | 21.340235 | 21.389070 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 2 | 18.881633 | 18.881633 | 19.871570 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 1 | 16.092148 | 16.092148 | 16.092148 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 21.418246 | 21.408145 | 21.432068 | 18.190524 | -15.07% | compared |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 9 | 15.589915 | 15.582603 | 15.642063 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 3 | 17.682321 | 17.672472 | 17.709316 | — | — | unresolved: prediction_deferred_by_population_priority |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 21.067549 | 21.057180 | 21.170037 | 18.251869 | -13.37% | compared |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 15.683328 | 15.670472 | 15.738329 | 13.267585 | -15.40% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; without separating that wait, elapsed time does not identify pure link bandwidth. The same observed boundary may calibrate per-call, per-group or payload-regime service responses. Explicit in-sample/heldout declarations are retained separately from contract eligibility; missing evaluation provenance remains not_declared.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528233 | 46.292617 | 0.235616 | 0.51% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.668964 | 37.413278 | 0.255686 | 0.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 37.705175 | 37.429031 | 0.276145 | 0.73% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 37.467978 | 37.200235 | 0.267743 | 0.71% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 38.396873 | 38.137811 | 0.259062 | 0.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 38.002127 | 37.736855 | 0.265272 | 0.70% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.713189 | 38.457571 | 0.255617 | 0.66% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 38.635279 | 38.374234 | 0.261045 | 0.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.030918 | 32.772932 | 0.257985 | 0.78% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 18.010107 | 17.748127 | 0.261980 | 1.45% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 15.697300 | 15.434811 | 0.262489 | 1.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 24.984322 | 24.715387 | 0.268936 | 1.08% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 33.211164 | 32.950234 | 0.260930 | 0.79% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 32.232000 | 31.960848 | 0.271152 | 0.84% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 31.922655 | 31.650425 | 0.272230 | 0.85% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 21.416720 | 21.144840 | 0.271880 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.616091 | 33.357768 | 0.258323 | 0.77% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 29.255343 | 28.989496 | 0.265847 | 0.91% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 21.440818 | 21.169837 | 0.270981 | 1.26% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 15.623967 | 15.363616 | 0.260350 | 1.67% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 33.357579 | 33.100602 | 0.256977 | 0.77% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 32.536283 | 32.271388 | 0.264895 | 0.81% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 24.989969 | 24.722395 | 0.267574 | 1.07% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 17.717363 | 17.455317 | 0.262046 | 1.48% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833324 | 28.568438 | 0.264886 | 0.92% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 25.112799 | 24.844953 | 0.267846 | 1.07% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 21.340235 | 21.068491 | 0.271744 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 18.881633 | 18.617714 | 0.263919 | 1.40% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 16.092148 | 15.828829 | 0.263319 | 1.64% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418246 | 21.147118 | 0.271128 | 1.27% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 15.589915 | 15.327661 | 0.262254 | 1.68% | not_established | 8 / 1 / 1 | auto / full |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 17.682321 | 17.420494 | 0.261827 | 1.48% | not_established | 8 / 1 / 1 | auto / full |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.067549 | 20.805273 | 0.262276 | 1.24% | not_established | 8 / 1 / 1 | none / full |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683328 | 15.421254 | 0.262074 | 1.67% | not_established | 8 / 1 / 1 | none / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | dense_layer | 2 / 3 | 0.496504 | 0.469962 | 0.550965 | 0.412777 | -16.86% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | moe_layer | 42 / 42 | 1.072327 | 0.889656 | 1.589585 | 1.091267 | +1.77% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | dense_layer | 0 / 3 | 0.397664 | 0.353061 | 0.487329 | 0.286118 | -28.05% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | moe_layer | 42 / 42 | 0.868453 | 0.754050 | 1.195816 | 0.816884 | -5.94% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | dense_layer | 0 / 3 | 0.398729 | 0.353734 | 0.489095 | 0.285091 | -28.50% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | moe_layer | 42 / 42 | 0.893239 | 0.753253 | 1.295158 | 0.841709 | -5.77% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | dense_layer | 0 / 3 | 0.331484 | 0.299064 | 0.397976 | 0.238974 | -27.91% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | moe_layer | 32 / 42 | 0.762750 | 0.680149 | 1.000371 | 0.688354 | -9.75% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | dense_layer | 0 / 3 | 0.327901 | 0.298229 | 0.387636 | 0.238688 | -27.21% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | moe_layer | 35 / 42 | 0.776939 | 0.678147 | 1.059929 | 0.702230 | -9.62% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | dense_layer | 0 / 3 | 0.334844 | 0.257668 | 0.497291 | 0.206551 | -38.31% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | moe_layer | 31 / 42 | 0.662567 | 0.593192 | 0.867922 | 0.590746 | -10.84% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | dense_layer | 0 / 3 | 0.264436 | 0.235357 | 0.323452 | 0.179060 | -32.29% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | moe_layer | 31 / 42 | 0.491047 | 0.428691 | 0.670685 | 0.420318 | -14.40% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | dense_layer | 0 / 3 | 0.313856 | 0.240144 | 0.464978 | 0.175129 | -44.20% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | moe_layer | 31 / 42 | 0.479167 | 0.424416 | 0.634057 | 0.422059 | -11.92% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | dense_layer | 0 / 3 | 0.306520 | 0.263452 | 0.422210 | 0.164530 | -46.32% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | moe_layer | 31 / 42 | 0.351495 | 0.302211 | 0.492130 | 0.304143 | -13.47% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 33 / 34 | 0.853091 | 0.886410 | 0.892277 | 0.856556 | +0.41% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 11 / 11 | 1.592925 | 1.584140 | 1.613101 | 1.631694 | +2.43% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 31 / 34 | 0.720522 | 0.752286 | 0.755426 | 0.676616 | -6.09% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 11 / 11 | 1.197294 | 1.193753 | 1.212146 | 1.105684 | -7.65% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 31 / 34 | 0.719759 | 0.750541 | 0.755133 | 0.675659 | -6.13% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 11 / 11 | 1.294585 | 1.290762 | 1.308970 | 1.203150 | -7.06% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 31 / 34 | 0.647355 | 0.676956 | 0.682362 | 0.599310 | -7.42% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 1 / 11 | 1.001808 | 0.997207 | 1.015218 | 0.841025 | -16.05% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 31 / 34 | 0.646030 | 0.676663 | 0.682706 | 0.598630 | -7.34% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 4 / 11 | 1.059101 | 1.055154 | 1.070667 | 0.896030 | -15.40% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 31 / 34 | 0.567253 | 0.588717 | 0.597100 | 0.524550 | -7.53% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0 / 11 | 0.867794 | 0.867858 | 0.875472 | 0.690574 | -20.42% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 31 / 34 | 0.412141 | 0.424787 | 0.432720 | 0.376376 | -8.68% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0 / 11 | 0.673135 | 0.669531 | 0.677515 | 0.490341 | -27.16% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 31 / 34 | 0.412816 | 0.421465 | 0.428909 | 0.382829 | -7.26% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0 / 11 | 0.639166 | 0.633990 | 0.657478 | 0.475970 | -25.53% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 31 / 34 | 0.301047 | 0.298533 | 0.305713 | 0.277435 | -7.84% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0 / 11 | 0.495159 | 0.491361 | 0.512266 | 0.348617 | -29.60% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 0.853091 | 0.848530 | 0.004561 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 1.592925 | 1.585690 | 0.007235 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 0.720522 | 0.715290 | 0.005232 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 1.197294 | 1.190310 | 0.006984 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 0.719759 | 0.714524 | 0.005234 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 1.294585 | 1.287614 | 0.006971 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 0.647355 | 0.642067 | 0.005288 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 1.001808 | 0.994786 | 0.007022 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 0.646030 | 0.640731 | 0.005298 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 1.059101 | 1.052082 | 0.007019 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 0.567253 | 0.562039 | 0.005215 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 0.867794 | 0.859921 | 0.007874 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 0.412141 | 0.406748 | 0.005393 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 0.673135 | 0.665243 | 0.007892 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 0.412816 | 0.407564 | 0.005253 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 0.639166 | 0.631647 | 0.007519 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 0.301047 | 0.295812 | 0.005235 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 0.495159 | 0.487604 | 0.007555 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | all | 44 | 1364 | 1.044916 | 0.888989 | 0.899502 | +1.18% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | kda | 33 | 1023 | 0.862246 | 0.886644 | 0.899502 | +1.45% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | mla | 11 | 341 | 1.592925 | 1.583919 | 1.631694 | +3.02% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | all | 44 | 1364 | 0.845015 | 0.753693 | 0.714406 | -5.21% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | kda | 33 | 1023 | 0.727589 | 0.752178 | 0.714406 | -5.02% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | mla | 11 | 341 | 1.197294 | 1.192474 | 1.105684 | -7.28% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | all | 44 | 1540 | 0.868707 | 0.752074 | 0.713456 | -5.13% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | kda | 33 | 1155 | 0.726748 | 0.750199 | 0.713456 | -4.90% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | mla | 11 | 385 | 1.294585 | 1.289925 | 1.203150 | -6.73% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | all | 44 | 1320 | 0.741636 | 0.679557 | 0.634181 | -6.68% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | kda | 33 | 990 | 0.654912 | 0.676975 | 0.634181 | -6.32% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | mla | 11 | 330 | 1.001808 | 0.997804 | 0.841025 | -15.71% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | all | 44 | 1408 | 0.755170 | 0.677909 | 0.633463 | -6.56% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | kda | 33 | 1056 | 0.653860 | 0.676787 | 0.633463 | -6.40% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | mla | 11 | 352 | 1.059101 | 1.054342 | 0.896030 | -15.02% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | all | 44 | 1320 | 0.643979 | 0.591855 | 0.555324 | -6.17% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | kda | 33 | 990 | 0.569374 | 0.588956 | 0.555324 | -5.71% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | mla | 11 | 330 | 0.867794 | 0.864061 | 0.690574 | -20.08% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | all | 44 | 484 | 0.479405 | 0.428782 | 0.395471 | -7.77% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | kda | 33 | 363 | 0.414829 | 0.424868 | 0.395471 | -6.92% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | mla | 11 | 121 | 0.673135 | 0.671351 | 0.490341 | -26.96% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | all | 44 | 2332 | 0.468218 | 0.423968 | 0.402930 | -4.96% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | kda | 33 | 1749 | 0.411236 | 0.421213 | 0.402930 | -4.34% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | mla | 11 | 583 | 0.639166 | 0.633678 | 0.475970 | -24.89% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | all | 44 | 2860 | 0.346822 | 0.301057 | 0.288362 | -4.22% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | kda | 33 | 2145 | 0.297376 | 0.298344 | 0.288362 | -3.35% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | mla | 11 | 715 | 0.495159 | 0.490270 | 0.348617 | -28.89% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 31 | 0.550965 | 0.529863 | 0.660172 | 0.412777 | -25.08% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 31 | 0.487329 | 0.462641 | 0.578271 | 0.286118 | -41.29% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 35 | 0.489095 | 0.481810 | 0.547052 | 0.285091 | -41.71% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 30 | 0.397976 | 0.393700 | 0.533420 | 0.238974 | -39.95% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 32 | 0.387636 | 0.401942 | 0.466389 | 0.238688 | -38.42% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 30 | 0.497291 | 0.498862 | 0.512161 | 0.206551 | -58.46% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 11 | 0.323452 | 0.280486 | 0.344031 | 0.179060 | -44.64% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 53 | 0.464978 | 0.474452 | 0.536593 | 0.175129 | -62.34% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 65 | 0.422210 | 0.438253 | 0.487926 | 0.164530 | -61.03% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 4 | 64 | 256 | unknown | 4104 | 64 | — | 29.828263 | — | 19.944121 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 4 | 32 | 128 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | 4 | 30 | 120 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | 4 | 24 | 96 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | 4 | 28 | 112 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | 4 | 26 | 104 | unknown | 4104 | 32 | — | 20.333395 | — | 15.440971 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 4 | 32 | 128 | unknown | 8200 | 32 | — | 25.049886 | — | 16.568588 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | 4 | 30 | 120 | unknown | 8200 | 32 | — | 25.049886 | — | 16.568588 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 4 | 16 | 64 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | 4 | 2 | 8 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | 4 | 6 | 24 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | 4 | 14 | 56 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | 4 | 12 | 48 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | 4 | 10 | 40 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 16 | — | 15.215758 | — | 13.615703 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 4 | 16 | 64 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | 4 | 8 | 32 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | 4 | 4 | 16 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | 4 | 1 | 4 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | 4 | 14 | 56 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | 4 | 12 | 48 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | 4 | 6 | 24 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | 4 | 2 | 8 | unknown | 8200 | 16 | — | 15.558226 | — | 13.679430 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 4 | 8 | 32 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | 4 | 6 | 24 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | 4 | 2 | 8 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 8 | — | 14.603654 | — | 12.080044 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 4 | 4 | 16 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | 4 | 1 | 4 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | 4 | 2 | 8 | unknown | 8200 | 4 | — | 12.932970 | — | 10.172629 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 4 | 4 | 16 | unknown | 4104 | 3 | — | 11.438829 | — | 9.752313 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 4 | 1 | 4 | unknown | 4104 | 1 | — | 8.534735 | — | 7.355036 |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | embedding | 31 | 0.005153 | 0.004906 | 0.006278 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | output_head_preparation | 31 | 0.009403 | 0.009451 | 0.009728 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | final_norm | 31 | 0.040726 | 0.040693 | 0.041491 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | lm_head | 31 | 0.107919 | 0.107887 | 0.108171 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | embedding | 31 | 0.004420 | 0.004263 | 0.005508 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | output_head_preparation | 31 | 0.007529 | 0.007544 | 0.007864 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | final_norm | 31 | 0.039866 | 0.039788 | 0.040637 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | lm_head | 31 | 0.101230 | 0.101196 | 0.101962 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | embedding | 2 | 0.004957 | 0.004957 | 0.005440 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | output_head_preparation | 2 | 0.010142 | 0.010142 | 0.010215 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | final_norm | 2 | 0.039856 | 0.039856 | 0.040493 |
| a5_glm53flash_tp8_c32_p4k:q4_b30_m120 | lm_head | 2 | 0.098706 | 0.098706 | 0.099093 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | embedding | 2 | 0.003968 | 0.003968 | 0.004134 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | output_head_preparation | 2 | 0.007030 | 0.007030 | 0.007152 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | final_norm | 2 | 0.039509 | 0.039509 | 0.039903 |
| a5_glm53flash_tp8_c32_p4k:q4_b24_m96 | lm_head | 2 | 0.095435 | 0.095435 | 0.095630 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | embedding | 1 | 0.004301 | 0.004301 | 0.004301 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | output_head_preparation | 1 | 0.007747 | 0.007747 | 0.007747 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | final_norm | 1 | 0.039215 | 0.039215 | 0.039215 |
| a5_glm53flash_tp8_c32_p4k:q4_b28_m112 | lm_head | 1 | 0.098549 | 0.098549 | 0.098549 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | embedding | 1 | 0.006187 | 0.006187 | 0.006187 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | output_head_preparation | 1 | 0.007494 | 0.007494 | 0.007494 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | final_norm | 1 | 0.040265 | 0.040265 | 0.040265 |
| a5_glm53flash_tp8_c32_p4k:q4_b26_m104 | lm_head | 1 | 0.096024 | 0.096024 | 0.096024 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | embedding | 35 | 0.004283 | 0.004021 | 0.005149 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | output_head_preparation | 35 | 0.007651 | 0.007655 | 0.007883 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | final_norm | 35 | 0.039854 | 0.039860 | 0.040524 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | lm_head | 35 | 0.100081 | 0.100014 | 0.100637 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | embedding | 1 | 0.004700 | 0.004700 | 0.004700 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | output_head_preparation | 1 | 0.009528 | 0.009528 | 0.009528 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | final_norm | 1 | 0.039851 | 0.039851 | 0.039851 |
| a5_glm53flash_tp8_c32_p8k:q4_b30_m120 | lm_head | 1 | 0.097564 | 0.097564 | 0.097564 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | embedding | 30 | 0.004553 | 0.004525 | 0.005564 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | output_head_preparation | 30 | 0.006682 | 0.006729 | 0.007088 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | final_norm | 30 | 0.040526 | 0.040494 | 0.041248 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | lm_head | 30 | 0.088715 | 0.088786 | 0.089602 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | embedding | 4 | 0.003420 | 0.003452 | 0.003850 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | output_head_preparation | 4 | 0.005153 | 0.005201 | 0.005332 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | final_norm | 4 | 0.034924 | 0.034920 | 0.035321 |
| a5_glm53flash_tp8_c16_p4k:q4_b2_m8 | lm_head | 4 | 0.049094 | 0.049037 | 0.049990 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | embedding | 3 | 0.002951 | 0.002885 | 0.003313 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | output_head_preparation | 3 | 0.005360 | 0.005500 | 0.005603 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | final_norm | 3 | 0.034749 | 0.034833 | 0.034835 |
| a5_glm53flash_tp8_c16_p4k:q4_b1_m4 | lm_head | 3 | 0.048303 | 0.048403 | 0.048578 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | embedding | 2 | 0.003848 | 0.003848 | 0.003962 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | output_head_preparation | 2 | 0.005883 | 0.005883 | 0.006297 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | final_norm | 2 | 0.038606 | 0.038606 | 0.039156 |
| a5_glm53flash_tp8_c16_p4k:q4_b6_m24 | lm_head | 2 | 0.049973 | 0.049973 | 0.050734 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | embedding | 1 | 0.004096 | 0.004096 | 0.004096 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | output_head_preparation | 1 | 0.007392 | 0.007392 | 0.007392 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | final_norm | 1 | 0.039928 | 0.039928 | 0.039928 |
| a5_glm53flash_tp8_c16_p4k:q4_b14_m56 | lm_head | 1 | 0.085771 | 0.085771 | 0.085771 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | embedding | 1 | 0.003766 | 0.003766 | 0.003766 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | output_head_preparation | 1 | 0.006667 | 0.006667 | 0.006667 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | final_norm | 1 | 0.040490 | 0.040490 | 0.040490 |
| a5_glm53flash_tp8_c16_p4k:q4_b12_m48 | lm_head | 1 | 0.059180 | 0.059180 | 0.059180 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | embedding | 1 | 0.002906 | 0.002906 | 0.002906 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | output_head_preparation | 1 | 0.007098 | 0.007098 | 0.007098 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | final_norm | 1 | 0.040217 | 0.040217 | 0.040217 |
| a5_glm53flash_tp8_c16_p4k:q4_b10_m40 | lm_head | 1 | 0.059376 | 0.059376 | 0.059376 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | embedding | 1 | 0.003926 | 0.003926 | 0.003926 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | output_head_preparation | 1 | 0.004996 | 0.004996 | 0.004996 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | final_norm | 1 | 0.036260 | 0.036260 | 0.036260 |
| a5_glm53flash_tp8_c16_p4k:q4_b4_m16 | lm_head | 1 | 0.049699 | 0.049699 | 0.049699 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | embedding | 32 | 0.004520 | 0.004431 | 0.005326 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | output_head_preparation | 32 | 0.006810 | 0.006925 | 0.007141 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | final_norm | 32 | 0.040588 | 0.040555 | 0.041123 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | lm_head | 32 | 0.088318 | 0.088529 | 0.089220 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | embedding | 2 | 0.003769 | 0.003769 | 0.004572 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | output_head_preparation | 2 | 0.006301 | 0.006301 | 0.006349 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | final_norm | 2 | 0.038984 | 0.038984 | 0.039594 |
| a5_glm53flash_tp8_c16_p8k:q4_b8_m32 | lm_head | 2 | 0.050176 | 0.050176 | 0.050733 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | embedding | 2 | 0.003302 | 0.003302 | 0.003438 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | output_head_preparation | 2 | 0.005175 | 0.005175 | 0.005456 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | final_norm | 2 | 0.036297 | 0.036297 | 0.036311 |
| a5_glm53flash_tp8_c16_p8k:q4_b4_m16 | lm_head | 2 | 0.050319 | 0.050319 | 0.050635 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | embedding | 2 | 0.003207 | 0.003207 | 0.003371 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | output_head_preparation | 2 | 0.005476 | 0.005476 | 0.005500 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | final_norm | 2 | 0.034876 | 0.034876 | 0.034992 |
| a5_glm53flash_tp8_c16_p8k:q4_b1_m4 | lm_head | 2 | 0.048877 | 0.048877 | 0.049106 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | embedding | 1 | 0.004029 | 0.004029 | 0.004029 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | output_head_preparation | 1 | 0.008101 | 0.008101 | 0.008101 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | final_norm | 1 | 0.039601 | 0.039601 | 0.039601 |
| a5_glm53flash_tp8_c16_p8k:q4_b14_m56 | lm_head | 1 | 0.084248 | 0.084248 | 0.084248 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | embedding | 1 | 0.003431 | 0.003431 | 0.003431 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | output_head_preparation | 1 | 0.005966 | 0.005966 | 0.005966 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | final_norm | 1 | 0.040585 | 0.040585 | 0.040585 |
| a5_glm53flash_tp8_c16_p8k:q4_b12_m48 | lm_head | 1 | 0.058436 | 0.058436 | 0.058436 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | embedding | 1 | 0.003757 | 0.003757 | 0.003757 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | output_head_preparation | 1 | 0.006379 | 0.006379 | 0.006379 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | final_norm | 1 | 0.038149 | 0.038149 | 0.038149 |
| a5_glm53flash_tp8_c16_p8k:q4_b6_m24 | lm_head | 1 | 0.050160 | 0.050160 | 0.050160 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | embedding | 1 | 0.002750 | 0.002750 | 0.002750 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | output_head_preparation | 1 | 0.005298 | 0.005298 | 0.005298 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | final_norm | 1 | 0.035537 | 0.035537 | 0.035537 |
| a5_glm53flash_tp8_c16_p8k:q4_b2_m8 | lm_head | 1 | 0.047421 | 0.047421 | 0.047421 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | embedding | 30 | 0.003182 | 0.003112 | 0.003608 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | output_head_preparation | 30 | 0.005864 | 0.005867 | 0.006163 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | final_norm | 30 | 0.039579 | 0.039516 | 0.040315 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | lm_head | 30 | 0.051001 | 0.050651 | 0.052626 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | embedding | 3 | 0.003911 | 0.003955 | 0.004103 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | output_head_preparation | 3 | 0.006226 | 0.006167 | 0.006562 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | final_norm | 3 | 0.037290 | 0.037535 | 0.037677 |
| a5_glm53flash_tp8_c8_p4k:q4_b6_m24 | lm_head | 3 | 0.049996 | 0.050208 | 0.050628 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | embedding | 2 | 0.003790 | 0.003790 | 0.004197 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | output_head_preparation | 2 | 0.005394 | 0.005394 | 0.005662 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | final_norm | 2 | 0.035840 | 0.035840 | 0.035918 |
| a5_glm53flash_tp8_c8_p4k:q4_b4_m16 | lm_head | 2 | 0.050087 | 0.050087 | 0.050191 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | embedding | 2 | 0.002894 | 0.002894 | 0.003096 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | output_head_preparation | 2 | 0.005300 | 0.005300 | 0.005735 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | final_norm | 2 | 0.035452 | 0.035452 | 0.035793 |
| a5_glm53flash_tp8_c8_p4k:q4_b2_m8 | lm_head | 2 | 0.048963 | 0.048963 | 0.049836 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | embedding | 1 | 0.003240 | 0.003240 | 0.003240 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | output_head_preparation | 1 | 0.004987 | 0.004987 | 0.004987 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | final_norm | 1 | 0.034165 | 0.034165 | 0.034165 |
| a5_glm53flash_tp8_c8_p4k:q4_b1_m4 | lm_head | 1 | 0.048935 | 0.048935 | 0.048935 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | embedding | 11 | 0.003148 | 0.003088 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | output_head_preparation | 11 | 0.005225 | 0.005255 | 0.005539 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | final_norm | 11 | 0.036308 | 0.036356 | 0.036607 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | lm_head | 11 | 0.050044 | 0.050001 | 0.050849 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | embedding | 9 | 0.002952 | 0.002875 | 0.003418 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | output_head_preparation | 9 | 0.005144 | 0.005175 | 0.005625 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | final_norm | 9 | 0.034639 | 0.034648 | 0.035308 |
| a5_glm53flash_tp8_c4_p8k:q4_b1_m4 | lm_head | 9 | 0.048629 | 0.048585 | 0.049569 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | embedding | 3 | 0.003078 | 0.003057 | 0.003300 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | output_head_preparation | 3 | 0.005326 | 0.005324 | 0.005616 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | final_norm | 3 | 0.034953 | 0.035107 | 0.035348 |
| a5_glm53flash_tp8_c4_p8k:q4_b2_m8 | lm_head | 3 | 0.049295 | 0.049272 | 0.049677 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | embedding | 53 | 0.004169 | 0.004090 | 0.004625 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | output_head_preparation | 53 | 0.005233 | 0.005053 | 0.005939 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | final_norm | 53 | 0.036160 | 0.036119 | 0.036702 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | lm_head | 53 | 0.049451 | 0.049313 | 0.050247 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | embedding | 65 | 0.003436 | 0.003402 | 0.003777 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | output_head_preparation | 65 | 0.005408 | 0.005362 | 0.005811 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | final_norm | 65 | 0.034594 | 0.034528 | 0.035106 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | lm_head | 65 | 0.048571 | 0.048453 | 0.049677 |

Summary: {"case_count": 34, "compared_cases": 9, "failed_cases": 0, "measured_cases": 34, "passed_cases": 7, "source_case_count": 9, "unresolved_cases": 25}
