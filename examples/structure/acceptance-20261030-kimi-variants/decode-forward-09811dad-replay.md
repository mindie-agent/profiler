# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "09811dad268203b6d021e01715b1c245d877c40f"}.

Sim 0.8.0; 228 package files; SHA256 `57d40b5b746923be0f725879f83825c3d4e428230ab72fa9bf920c0fde5d3360`; package `/Users/maoxx241/code/sim-rewrite-20261027/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 3.180250 | 3.127828 | 3.431912 | 3.236926 | +1.78% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 4.807080 | 4.779005 | 4.992080 | 4.457327 | -7.28% | compared |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3 | 3.844777 | 3.280615 | 5.439251 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 6.713782 | 6.664787 | 6.922921 | 6.593744 | -1.79% | compared |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3 | 3.240302 | 3.278234 | 3.410932 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3 | 3.363853 | 3.379593 | 3.466951 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 3.812064 | 3.812064 | 3.812064 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2.978001 | 2.978001 | 2.978001 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 4.690486 | 4.690486 | 4.690486 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 3.476353 | 3.437971 | 3.655687 | 3.296926 | -5.16% | compared |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 4 | 3.375663 | 3.346474 | 3.556049 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3 | 3.190596 | 3.244875 | 3.293894 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 9.615404 | 9.549549 | 9.774245 | 10.146868 | +5.53% | compared |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3 | 3.178496 | 3.253895 | 3.501150 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 2 | 8.472921 | 8.472921 | 8.559829 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 2 | 5.631388 | 5.631388 | 5.719806 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 2 | 4.722715 | 4.722715 | 4.738645 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 3.160037 | 3.160037 | 3.160037 | — | — | unresolved: prediction_deferred_by_population_priority |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 3.536929 | 3.536929 | 3.536929 | — | — | unresolved: prediction_deferred_by_population_priority |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 39.247386 | 39.244948 | 39.262920 | 27.912977 | -28.88% | compared |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 36.985292 | 36.952793 | 36.968819 | 26.702652 | -27.80% | compared |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 30.823435 | 30.822007 | 30.838985 | 23.618433 | -23.38% | compared |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 30.636854 | 30.614967 | 30.632466 | 23.542787 | -23.16% | compared |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 33.875753 | 33.857996 | 33.873078 | 23.840832 | -29.62% | compared |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 33.547630 | 33.515767 | 33.532651 | 23.689541 | -29.39% | compared |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 33.088625 | -25.92% | compared |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 30.667975 | -23.37% | compared |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 34.816498 | 34.793753 | 34.812948 | 24.285631 | -30.25% | compared |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 34.193709 | 34.177425 | 34.194190 | 23.983049 | -29.86% | compared |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 35.964417 | 35.962094 | 35.978788 | 25.173916 | -30.00% | compared |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 34.819213 | 34.791110 | 34.808453 | 24.568753 | -29.44% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180250 | 3.088476 | 0.091774 | 2.89% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 4.807080 | 4.709462 | 0.097618 | 2.03% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 3.844777 | 3.742211 | 0.102565 | 2.67% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.713782 | 6.609395 | 0.104386 | 1.55% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 3.240302 | 3.159277 | 0.081025 | 2.50% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 3.363853 | 3.282654 | 0.081199 | 2.41% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 3.812064 | 3.719127 | 0.092937 | 2.44% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 2.978001 | 2.886602 | 0.091399 | 3.07% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 4.690486 | 4.604887 | 0.085599 | 1.82% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 3.476353 | 3.379951 | 0.096402 | 2.77% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 3.375663 | 3.281668 | 0.093994 | 2.78% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 3.190596 | 3.093745 | 0.096851 | 3.04% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 9.615404 | 9.502317 | 0.113087 | 1.18% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 3.178496 | 3.096751 | 0.081745 | 2.57% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 8.472921 | 8.364464 | 0.108457 | 1.28% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 5.631388 | 5.531740 | 0.099647 | 1.77% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 4.722715 | 4.622307 | 0.100409 | 2.13% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 3.160037 | 3.069540 | 0.090497 | 2.86% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 3.536929 | 3.456050 | 0.080879 | 2.29% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247386 | 38.566577 | 0.680809 | 1.73% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985292 | 36.304665 | 0.680627 | 1.84% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823435 | 30.183881 | 0.639554 | 2.07% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.636854 | 29.997042 | 0.639813 | 2.09% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.875753 | 33.190409 | 0.685344 | 2.02% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.547630 | 32.856947 | 0.690684 | 2.06% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666193 | 43.970836 | 0.695357 | 1.56% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.018728 | 39.322926 | 0.695802 | 1.74% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816498 | 34.115094 | 0.701404 | 2.01% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.193709 | 33.491477 | 0.702232 | 2.05% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964417 | 35.281594 | 0.682823 | 1.90% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819213 | 34.142215 | 0.676998 | 1.94% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | dense_layer | 0 / 1 | 0.921918 | 0.921918 | 0.921918 | 0.567487 | -38.44% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | moe_layer | 2 / 3 | 0.796936 | 0.814264 | 0.835939 | 0.882975 | +10.80% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | dense_layer | 0 / 1 | 0.902124 | 0.902124 | 0.902124 | 0.667808 | -25.97% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | moe_layer | 2 / 3 | 1.336028 | 1.365465 | 1.453488 | 1.256999 | -5.92% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | dense_layer | 1 / 1 | 0.884665 | 0.884665 | 0.884665 | 0.794060 | -10.24% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | moe_layer | 3 / 3 | 1.963693 | 1.922699 | 2.172615 | 1.926712 | -1.88% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | dense_layer | 0 / 1 | 0.868805 | 0.868805 | 0.868805 | 0.582487 | -32.96% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | moe_layer | 3 / 3 | 0.916748 | 0.941859 | 0.968316 | 0.897975 | -2.05% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | dense_layer | 1 / 1 | 0.960436 | 0.960436 | 0.960436 | 1.046602 | +8.97% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | moe_layer | 3 / 3 | 2.917340 | 2.803217 | 3.209222 | 3.026223 | +3.73% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | dense_layer | 1 / 1 | 0.304707 | 0.304707 | 0.304707 | 0.262223 | -13.94% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | moe_layer | 0 / 92 | 0.423260 | 0.387824 | 0.524838 | 0.300409 | -29.02% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | dense_layer | 0 / 1 | 0.335331 | 0.335331 | 0.335331 | 0.262223 | -21.80% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | moe_layer | 0 / 92 | 0.398339 | 0.387665 | 0.429149 | 0.287253 | -27.89% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | dense_layer | 1 / 1 | 0.259493 | 0.259493 | 0.259493 | 0.228650 | -11.89% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | moe_layer | 0 / 92 | 0.332185 | 0.322766 | 0.359609 | 0.254083 | -23.51% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | dense_layer | 0 / 1 | 0.277218 | 0.277218 | 0.277218 | 0.228650 | -17.52% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | moe_layer | 0 / 92 | 0.329965 | 0.323096 | 0.350795 | 0.253261 | -23.25% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | dense_layer | 0 / 1 | 0.287557 | 0.287557 | 0.287557 | 0.230228 | -19.94% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | moe_layer | 0 / 92 | 0.365059 | 0.354655 | 0.392704 | 0.256483 | -29.74% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | dense_layer | 0 / 1 | 0.302651 | 0.302651 | 0.302651 | 0.230228 | -23.93% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | moe_layer | 0 / 92 | 0.361328 | 0.354921 | 0.377885 | 0.254839 | -29.47% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 0 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.305513 | -15.61% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 0 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.356190 | -26.03% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 1 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.305513 | -9.59% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 0 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.329879 | -23.51% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | dense_layer | 0 / 1 | 0.297407 | 0.297407 | 0.297407 | 0.233384 | -21.53% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | moe_layer | 0 / 92 | 0.375177 | 0.361169 | 0.412914 | 0.261283 | -30.36% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | dense_layer | 0 / 1 | 0.293014 | 0.293014 | 0.293014 | 0.233384 | -20.35% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | moe_layer | 0 / 92 | 0.368455 | 0.361005 | 0.387096 | 0.257995 | -29.98% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | dense_layer | 0 / 1 | 0.284019 | 0.284019 | 0.284019 | 0.239696 | -15.61% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | moe_layer | 0 / 92 | 0.387800 | 0.367269 | 0.446146 | 0.270884 | -30.15% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | dense_layer | 0 / 1 | 0.310159 | 0.310159 | 0.310159 | 0.239696 | -22.72% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | moe_layer | 0 / 92 | 0.375068 | 0.367254 | 0.397893 | 0.264307 | -29.53% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 1 / 3 | 0.825596 | 0.814264 | 0.921918 | 0.792611 | -4.00% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 / 1 | 0.835939 | 0.835939 | 0.835939 | 0.838581 | +0.32% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 / 3 | 1.152240 | 1.189132 | 1.365465 | 1.076756 | -6.55% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 0 / 1 | 1.453488 | 1.453488 | 1.453488 | 1.208536 | -16.85% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 3 / 3 | 1.534376 | 1.795764 | 1.922699 | 1.567053 | +2.13% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 / 1 | 2.172615 | 2.172615 | 2.172615 | 1.873038 | -13.79% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 / 3 | 0.883578 | 0.868805 | 0.941859 | 0.807611 | -8.60% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 1 / 1 | 0.968316 | 0.968316 | 0.968316 | 0.853581 | -11.85% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 3 / 3 | 2.167745 | 2.739582 | 2.803217 | 2.387724 | +10.15% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 / 1 | 3.209222 | 3.209222 | 3.209222 | 2.962101 | -7.70% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 1 / 69 | 0.384646 | 0.385628 | 0.391398 | 0.293908 | -23.59% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0 / 24 | 0.529336 | 0.522407 | 0.529076 | 0.317508 | -40.02% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0 / 69 | 0.385013 | 0.385311 | 0.391916 | 0.293908 | -23.66% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0 / 24 | 0.434026 | 0.426707 | 0.433591 | 0.267078 | -38.46% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 1 / 69 | 0.319910 | 0.320784 | 0.326143 | 0.259332 | -18.94% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0 / 24 | 0.364449 | 0.357714 | 0.364380 | 0.237931 | -34.71% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0 / 69 | 0.320268 | 0.320936 | 0.326067 | 0.259332 | -19.03% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0 / 24 | 0.355645 | 0.348782 | 0.355492 | 0.234779 | -33.98% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0 / 69 | 0.352160 | 0.352714 | 0.358215 | 0.260910 | -25.91% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0 / 24 | 0.398913 | 0.391929 | 0.399012 | 0.242661 | -39.17% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0 / 69 | 0.352595 | 0.353094 | 0.358531 | 0.260910 | -26.00% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0 / 24 | 0.383988 | 0.376708 | 0.384608 | 0.236357 | -38.45% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.337341 | -18.46% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.408271 | -39.20% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 1 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.337341 | -18.33% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.307410 | -35.94% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0 / 69 | 0.358721 | 0.359340 | 0.364725 | 0.264066 | -26.39% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0 / 24 | 0.419247 | 0.412473 | 0.418457 | 0.252121 | -39.86% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0 / 69 | 0.358666 | 0.359601 | 0.365194 | 0.264066 | -26.38% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0 / 24 | 0.393454 | 0.386399 | 0.392108 | 0.239513 | -39.13% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0 / 69 | 0.364080 | 0.364932 | 0.370969 | 0.270378 | -25.74% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0 / 24 | 0.451672 | 0.445328 | 0.451445 | 0.271040 | -39.99% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0 / 69 | 0.364444 | 0.364580 | 0.370731 | 0.270378 | -25.81% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0 / 24 | 0.402906 | 0.396176 | 0.402359 | 0.245825 | -38.99% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 0.825596 | 0.811190 | 0.014406 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 0.835939 | 0.784698 | 0.051240 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 1.152240 | 1.136963 | 0.015278 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1.453488 | 1.399692 | 0.053796 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 1.534376 | 1.517276 | 0.017100 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 2.172615 | 2.118742 | 0.053873 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 0.883578 | 0.868957 | 0.014621 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 0.968316 | 0.912434 | 0.055882 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2.167745 | 2.147499 | 0.020246 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 3.209222 | 3.155193 | 0.054029 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0.384646 | 0.379054 | 0.005591 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0.529336 | 0.517159 | 0.012177 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0.385013 | 0.379424 | 0.005589 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0.434026 | 0.421850 | 0.012176 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0.319910 | 0.314950 | 0.004960 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0.364449 | 0.352180 | 0.012269 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0.320268 | 0.315305 | 0.004963 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0.355645 | 0.343375 | 0.012270 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0.352160 | 0.346560 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0.398913 | 0.386575 | 0.012338 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0.352595 | 0.346938 | 0.005657 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0.383988 | 0.371592 | 0.012396 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0.413723 | 0.407971 | 0.005752 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0.671523 | 0.659202 | 0.012321 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0.413032 | 0.407278 | 0.005754 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0.479865 | 0.467530 | 0.012334 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0.358721 | 0.352935 | 0.005785 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0.419247 | 0.406773 | 0.012474 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0.358666 | 0.352873 | 0.005793 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0.393454 | 0.380967 | 0.012487 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0.364080 | 0.358480 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0.451672 | 0.439438 | 0.012234 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0.364444 | 0.358904 | 0.005540 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0.402906 | 0.390743 | 0.012163 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | all | 3 | 762 | 0.796936 | 0.776385 | 0.905172 | +16.59% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | kda | 2 | 508 | 0.777435 | 0.725436 | 0.905172 | +24.78% |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | mla | 1 | 254 | 0.835939 | 0.799415 | 0.838581 | +4.90% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | all | 3 | 705 | 1.336028 | 1.346153 | 1.281230 | -4.82% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | kda | 2 | 470 | 1.277298 | 1.265664 | 1.281230 | +1.23% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | mla | 1 | 235 | 1.453488 | 1.452451 | 1.208536 | -16.79% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | all | 3 | 660 | 1.963693 | 1.885652 | 1.953549 | +3.60% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | kda | 2 | 440 | 1.859231 | 1.840788 | 1.953549 | +6.13% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | mla | 1 | 220 | 2.172615 | 2.172336 | 1.873038 | -13.78% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | all | 3 | 738 | 0.916748 | 0.892432 | 0.920172 | +3.11% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | kda | 2 | 492 | 0.890964 | 0.848128 | 0.920172 | +8.49% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | mla | 1 | 246 | 0.968316 | 0.961650 | 0.853581 | -11.24% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | all | 3 | 588 | 2.917340 | 2.774904 | 3.058284 | +10.21% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | kda | 2 | 392 | 2.771399 | 2.756885 | 3.058284 | +10.93% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | mla | 1 | 196 | 3.209222 | 3.208946 | 2.962101 | -7.69% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | all | 92 | 4324 | 0.423260 | 0.387808 | 0.295450 | -23.82% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 68 | 3196 | 0.385821 | 0.385597 | 0.293701 | -23.83% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 24 | 1128 | 0.529336 | 0.522342 | 0.317145 | -39.28% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | all | 92 | 4508 | 0.398339 | 0.387570 | 0.292920 | -24.42% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 68 | 3332 | 0.385744 | 0.385530 | 0.293701 | -23.82% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 24 | 1176 | 0.434026 | 0.426871 | 0.266714 | -37.52% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | all | 92 | 5428 | 0.332185 | 0.322654 | 0.259675 | -19.52% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 68 | 4012 | 0.320798 | 0.320809 | 0.259675 | -19.06% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 24 | 1416 | 0.364449 | 0.357739 | 0.237791 | -33.53% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | all | 92 | 5428 | 0.329965 | 0.323043 | 0.259675 | -19.62% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 68 | 4012 | 0.320901 | 0.321012 | 0.259675 | -19.11% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 24 | 1416 | 0.355645 | 0.348701 | 0.234639 | -32.71% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | all | 92 | 4968 | 0.365059 | 0.354617 | 0.261253 | -26.33% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 68 | 3672 | 0.353110 | 0.352903 | 0.261253 | -25.97% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 24 | 1296 | 0.398913 | 0.391767 | 0.242521 | -38.10% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | all | 92 | 5060 | 0.361328 | 0.354858 | 0.261253 | -26.38% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 68 | 3740 | 0.353330 | 0.353148 | 0.261253 | -26.02% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 24 | 1320 | 0.383988 | 0.376723 | 0.236217 | -37.30% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.339025 | -18.47% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.339025 | -18.15% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.409449 | -38.37% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.337301 | -18.79% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.339025 | -18.12% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.308589 | -34.65% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | all | 92 | 4784 | 0.375177 | 0.361188 | 0.264409 | -26.79% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 68 | 3536 | 0.359622 | 0.359235 | 0.264409 | -26.40% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 24 | 1248 | 0.419247 | 0.412474 | 0.251980 | -38.91% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | all | 92 | 4876 | 0.368455 | 0.361070 | 0.264409 | -26.77% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 68 | 3604 | 0.359632 | 0.359552 | 0.264409 | -26.46% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 24 | 1272 | 0.393454 | 0.386327 | 0.239373 | -38.04% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | all | 92 | 4692 | 0.387800 | 0.367070 | 0.270721 | -26.25% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 68 | 3468 | 0.365257 | 0.364968 | 0.270721 | -25.82% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 24 | 1224 | 0.451672 | 0.445448 | 0.270900 | -39.18% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | all | 92 | 4784 | 0.375068 | 0.366904 | 0.270721 | -26.21% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 68 | 3536 | 0.365243 | 0.364788 | 0.270721 | -25.79% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 24 | 1248 | 0.402906 | 0.395987 | 0.245685 | -37.96% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 254 | 0.921918 | 0.911601 | 1.011820 | 0.567487 | -38.44% |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 235 | 0.902124 | 0.935902 | 1.032420 | 0.667808 | -25.97% |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 220 | 0.884665 | 0.918071 | 1.035580 | 0.794060 | -10.24% |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 246 | 0.868805 | 0.892722 | 0.986620 | 0.582487 | -32.96% |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 196 | 0.960436 | 0.952631 | 1.021539 | 1.046602 | +8.97% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 0.304707 | 0.302280 | 0.304417 | 0.262223 | -13.94% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 0.335331 | 0.302283 | 0.304588 | 0.262223 | -21.80% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 0.259493 | 0.258140 | 0.259720 | 0.228650 | -11.89% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 0.277218 | 0.257813 | 0.259545 | 0.228650 | -17.52% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 0.287557 | 0.269792 | 0.271359 | 0.230228 | -19.94% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 0.302651 | 0.269840 | 0.271908 | 0.230228 | -23.93% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.305513 | -15.61% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.305513 | -9.59% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 0.297407 | 0.276998 | 0.278997 | 0.233384 | -21.53% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 0.293014 | 0.277106 | 0.279247 | 0.233384 | -20.35% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 0.284019 | 0.281037 | 0.283397 | 0.239696 | -15.61% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 0.310159 | 0.281559 | 0.283741 | 0.239696 | -22.72% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 1 | 7.167215 | 7.167215 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 16 | 8.646915 | 8.627808 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 1 | 32 | 32 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | 1 | 8 | 8 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 32 | 9.790394 | 9.771368 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 4 | 7.450663 | 7.475983 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | 1 | 64 | 64 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | 1 | 1 | 1 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | 1 | 48 | 48 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | 1 | 24 | 24 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | 1 | 16 | 16 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | 1 | 2 | 2 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | 1 | 4 | 4 | unknown | 4096 | 64 | 14.068943 | 14.183905 | — | — |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 1 | 16 | 16 | unknown | 16392 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 1 | 16 | 16 | unknown | 4104 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 1 | 1 | 1 | unknown | 16392 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 1 | 1 | 1 | unknown | 4104 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 1 | 2 | 2 | unknown | 16392 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 1 | 2 | 2 | unknown | 4104 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 1 | 32 | 32 | unknown | 16392 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 1 | 32 | 32 | unknown | 4104 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 1 | 4 | 4 | unknown | 16392 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 1 | 4 | 4 | unknown | 4104 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 1 | 8 | 8 | unknown | 16392 | 8 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 1 | 8 | 8 | unknown | 4104 | 8 | — | — | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | embedding | 254 | 0.009523 | 0.009420 | 0.009740 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | final_norm | 254 | 0.003637 | 0.003640 | 0.003700 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | lm_head | 254 | 0.275756 | 0.275744 | 0.278314 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | embedding | 235 | 0.005061 | 0.005020 | 0.005320 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | final_norm | 235 | 0.006631 | 0.006500 | 0.006819 |
| a3_kimi4_tp8_w4a8_c16:q1_b16_m16 | lm_head | 235 | 0.312556 | 0.312613 | 0.316314 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | embedding | 3 | 0.009047 | 0.009080 | 0.009300 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | final_norm | 3 | 0.003587 | 0.003580 | 0.003600 |
| a3_kimi4_tp8_w4a8_c16:q1_b1_m1 | lm_head | 3 | 0.276741 | 0.277055 | 0.278654 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | embedding | 220 | 0.009116 | 0.009080 | 0.009420 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | final_norm | 220 | 0.009454 | 0.009280 | 0.009460 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | lm_head | 220 | 0.313890 | 0.313543 | 0.317654 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | embedding | 3 | 0.009493 | 0.009499 | 0.009760 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | final_norm | 3 | 0.003600 | 0.003600 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b1_m1 | lm_head | 3 | 0.277841 | 0.276815 | 0.280234 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | embedding | 3 | 0.003020 | 0.002940 | 0.003300 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | final_norm | 3 | 0.004353 | 0.004400 | 0.004440 |
| a3_kimi4_tp8_w4a8_c32:q1_b4_m4 | lm_head | 3 | 0.284234 | 0.285574 | 0.285794 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | embedding | 1 | 0.003660 | 0.003660 | 0.003660 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | final_norm | 1 | 0.004940 | 0.004940 | 0.004940 |
| a3_kimi4_tp8_w4a8_c32:q1_b8_m8 | lm_head | 1 | 0.292854 | 0.292854 | 0.292854 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | embedding | 1 | 0.002720 | 0.002720 | 0.002720 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | final_norm | 1 | 0.003840 | 0.003840 | 0.003840 |
| a3_kimi4_tp8_w4a8_c32:q1_b2_m2 | lm_head | 1 | 0.280574 | 0.280574 | 0.280574 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | embedding | 1 | 0.005100 | 0.005100 | 0.005100 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | final_norm | 1 | 0.006300 | 0.006300 | 0.006300 |
| a3_kimi4_tp8_w4a8_c32:q1_b16_m16 | lm_head | 1 | 0.317034 | 0.317034 | 0.317034 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | embedding | 246 | 0.003053 | 0.003040 | 0.003319 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | final_norm | 246 | 0.004334 | 0.004320 | 0.004480 |
| a3_kimi4_tp8_w4a8_c4:q1_b4_m4 | lm_head | 246 | 0.284209 | 0.284254 | 0.287035 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | embedding | 4 | 0.002780 | 0.002780 | 0.002980 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | final_norm | 4 | 0.003945 | 0.003949 | 0.004000 |
| a3_kimi4_tp8_w4a8_c4:q1_b2_m2 | lm_head | 4 | 0.282285 | 0.282095 | 0.286114 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | embedding | 3 | 0.009247 | 0.009240 | 0.009300 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | final_norm | 3 | 0.003627 | 0.003640 | 0.003660 |
| a3_kimi4_tp8_w4a8_c4:q1_b1_m1 | lm_head | 3 | 0.275981 | 0.276014 | 0.276755 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | embedding | 196 | 0.009384 | 0.009360 | 0.009680 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | final_norm | 196 | 0.010675 | 0.010400 | 0.010640 |
| a3_kimi4_tp8_w4a8_c64:q1_b64_m64 | lm_head | 196 | 0.329141 | 0.328854 | 0.332534 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | embedding | 3 | 0.008933 | 0.008899 | 0.009060 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | final_norm | 3 | 0.003567 | 0.003560 | 0.003580 |
| a3_kimi4_tp8_w4a8_c64:q1_b1_m1 | lm_head | 3 | 0.276587 | 0.276014 | 0.279314 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | embedding | 2 | 0.006850 | 0.006850 | 0.007000 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | final_norm | 2 | 0.009080 | 0.009080 | 0.009199 |
| a3_kimi4_tp8_w4a8_c64:q1_b48_m48 | lm_head | 2 | 0.320554 | 0.320554 | 0.320933 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | embedding | 2 | 0.006979 | 0.006979 | 0.007100 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | final_norm | 2 | 0.008540 | 0.008540 | 0.008640 |
| a3_kimi4_tp8_w4a8_c64:q1_b24_m24 | lm_head | 2 | 0.307554 | 0.307554 | 0.309354 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | embedding | 2 | 0.005020 | 0.005020 | 0.005060 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | final_norm | 2 | 0.007720 | 0.007720 | 0.008960 |
| a3_kimi4_tp8_w4a8_c64:q1_b16_m16 | lm_head | 2 | 0.310954 | 0.310954 | 0.311894 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | embedding | 1 | 0.002520 | 0.002520 | 0.002520 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | final_norm | 1 | 0.004000 | 0.004000 | 0.004000 |
| a3_kimi4_tp8_w4a8_c64:q1_b2_m2 | lm_head | 1 | 0.287334 | 0.287334 | 0.287334 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | embedding | 1 | 0.002840 | 0.002840 | 0.002840 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | final_norm | 1 | 0.004400 | 0.004400 | 0.004400 |
| a3_kimi4_tp8_w4a8_c64:q1_b4_m4 | lm_head | 1 | 0.281494 | 0.281494 | 0.281494 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | embedding | 47 | 0.004621 | 0.004452 | 0.005158 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | final_norm | 47 | 0.004149 | 0.004128 | 0.004346 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | lm_head | 47 | 0.092373 | 0.092297 | 0.093138 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | embedding | 49 | 0.004593 | 0.004509 | 0.005168 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | final_norm | 49 | 0.004091 | 0.004082 | 0.004295 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | lm_head | 49 | 0.092424 | 0.092431 | 0.093127 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | embedding | 59 | 0.003153 | 0.003145 | 0.003345 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | final_norm | 59 | 0.002648 | 0.002644 | 0.002801 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | lm_head | 59 | 0.090694 | 0.090708 | 0.091441 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | embedding | 59 | 0.003171 | 0.003139 | 0.003410 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | final_norm | 59 | 0.002656 | 0.002643 | 0.002785 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | lm_head | 59 | 0.090801 | 0.090715 | 0.091604 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | embedding | 54 | 0.003248 | 0.003227 | 0.003438 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | final_norm | 54 | 0.003575 | 0.003547 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | lm_head | 54 | 0.090737 | 0.090634 | 0.091393 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | embedding | 55 | 0.003310 | 0.003279 | 0.003502 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | final_norm | 55 | 0.003606 | 0.003582 | 0.003776 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | lm_head | 55 | 0.090726 | 0.090704 | 0.091558 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | embedding | 41 | 0.003452 | 0.003466 | 0.003683 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | final_norm | 41 | 0.005865 | 0.005876 | 0.006045 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | lm_head | 41 | 0.117608 | 0.117655 | 0.118201 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | embedding | 46 | 0.003423 | 0.003405 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | final_norm | 46 | 0.005558 | 0.005548 | 0.005768 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | lm_head | 46 | 0.117594 | 0.117492 | 0.118427 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | embedding | 52 | 0.004307 | 0.004195 | 0.004880 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | final_norm | 52 | 0.003656 | 0.003638 | 0.003791 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | lm_head | 52 | 0.091122 | 0.090941 | 0.091927 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | embedding | 53 | 0.004472 | 0.004372 | 0.005045 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | final_norm | 53 | 0.003639 | 0.003622 | 0.003763 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | lm_head | 53 | 0.091033 | 0.090857 | 0.091549 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | embedding | 51 | 0.004301 | 0.004254 | 0.004600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | final_norm | 51 | 0.003739 | 0.003723 | 0.003842 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | lm_head | 51 | 0.091241 | 0.091220 | 0.091749 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | embedding | 52 | 0.004275 | 0.004245 | 0.004557 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | final_norm | 52 | 0.003738 | 0.003722 | 0.003837 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | lm_head | 52 | 0.091316 | 0.091258 | 0.092021 |

Summary: {"case_count": 31, "compared_cases": 17, "failed_cases": 0, "measured_cases": 31, "passed_cases": 5, "source_case_count": 17, "unresolved_cases": 14}
