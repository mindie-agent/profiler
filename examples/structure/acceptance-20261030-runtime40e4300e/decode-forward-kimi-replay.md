# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "40e4300ea7ccc1123759f6201cc2d69e3aa77ad6"}.

Variant: `body-runtime40e4300e-kimi`. Baseline: null.

Sim 0.8.0; 271 package files; SHA256 `ab51c56356b3b6f11a130dd7a59d2fd894b99148d0917fc4cc40189102286124`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 39.247386 | 39.244948 | 39.262920 | 28.209447 | -28.12% | compared |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 36.985292 | 36.952793 | 36.968819 | 25.616089 | -30.74% | compared |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 30.823435 | 30.822007 | 30.838985 | 23.553350 | -23.59% | compared |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 30.636854 | 30.614967 | 30.632466 | 23.391264 | -23.65% | compared |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 33.875753 | 33.857996 | 33.873078 | 23.835845 | -29.64% | compared |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 33.547630 | 33.515767 | 33.532651 | 23.515499 | -29.90% | compared |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 33.730514 | -24.48% | compared |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 40.018728 | 40.017751 | 40.043741 | 28.543760 | -28.67% | compared |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 34.816498 | 34.793753 | 34.812948 | 24.384306 | -29.96% | compared |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 34.193709 | 34.177425 | 34.194190 | 23.752987 | -30.53% | compared |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 35.964417 | 35.962094 | 35.978788 | 25.458716 | -29.21% | compared |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 34.819213 | 34.791110 | 34.808453 | 24.198061 | -30.50% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
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
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | dense_layer | 0 / 1 | 0.304707 | 0.304707 | 0.304707 | 0.226067 | -25.81% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | moe_layer | 0 / 92 | 0.423260 | 0.387824 | 0.524838 | 0.304025 | -28.17% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | dense_layer | 0 / 1 | 0.335331 | 0.335331 | 0.335331 | 0.226067 | -32.58% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | moe_layer | 0 / 92 | 0.398339 | 0.387665 | 0.429149 | 0.275836 | -30.75% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | dense_layer | 0 / 1 | 0.259493 | 0.259493 | 0.259493 | 0.207326 | -20.10% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | moe_layer | 0 / 92 | 0.332185 | 0.322766 | 0.359609 | 0.253607 | -23.65% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | dense_layer | 0 / 1 | 0.277218 | 0.277218 | 0.277218 | 0.207326 | -25.21% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | moe_layer | 0 / 92 | 0.329965 | 0.323096 | 0.350795 | 0.251845 | -23.68% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | dense_layer | 0 / 1 | 0.287557 | 0.287557 | 0.287557 | 0.207960 | -27.68% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | moe_layer | 0 / 92 | 0.365059 | 0.354655 | 0.392704 | 0.256671 | -29.69% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | dense_layer | 0 / 1 | 0.302651 | 0.302651 | 0.302651 | 0.207960 | -31.29% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | moe_layer | 0 / 92 | 0.361328 | 0.354921 | 0.377885 | 0.253189 | -29.93% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 0 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.253372 | -30.01% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 0 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.363734 | -24.46% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | dense_layer | 0 / 1 | 0.337916 | 0.337916 | 0.337916 | 0.253372 | -25.02% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | moe_layer | 0 / 92 | 0.431283 | 0.415274 | 0.473567 | 0.307356 | -28.73% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | dense_layer | 0 / 1 | 0.297407 | 0.297407 | 0.297407 | 0.209513 | -29.55% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | moe_layer | 0 / 92 | 0.375177 | 0.361169 | 0.412914 | 0.262615 | -30.00% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | dense_layer | 0 / 1 | 0.293014 | 0.293014 | 0.293014 | 0.209513 | -28.50% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | moe_layer | 0 / 92 | 0.368455 | 0.361005 | 0.387096 | 0.255753 | -30.59% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | dense_layer | 0 / 1 | 0.284019 | 0.284019 | 0.284019 | 0.213375 | -24.87% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | moe_layer | 0 / 92 | 0.387800 | 0.367269 | 0.446146 | 0.274266 | -29.28% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | dense_layer | 0 / 1 | 0.310159 | 0.310159 | 0.310159 | 0.213375 | -31.20% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | moe_layer | 0 / 92 | 0.375068 | 0.367254 | 0.397893 | 0.260563 | -30.53% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0 / 69 | 0.384646 | 0.385628 | 0.391398 | 0.274407 | -28.66% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0 / 24 | 0.529336 | 0.522407 | 0.529076 | 0.385926 | -27.09% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 0 / 69 | 0.385013 | 0.385311 | 0.391916 | 0.274407 | -28.73% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 0 / 24 | 0.434026 | 0.426707 | 0.433591 | 0.277869 | -35.98% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0 / 69 | 0.319910 | 0.320784 | 0.326143 | 0.256457 | -19.83% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0 / 24 | 0.364449 | 0.357714 | 0.364380 | 0.243487 | -33.19% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 0 / 69 | 0.320268 | 0.320936 | 0.326067 | 0.256457 | -19.92% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 0 / 24 | 0.355645 | 0.348782 | 0.355492 | 0.236733 | -33.44% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0 / 69 | 0.352160 | 0.352714 | 0.358215 | 0.257091 | -27.00% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0 / 24 | 0.398913 | 0.391929 | 0.399012 | 0.253435 | -36.47% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 0 / 69 | 0.352595 | 0.353094 | 0.358531 | 0.257091 | -27.09% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 0 / 24 | 0.383988 | 0.376708 | 0.384608 | 0.240087 | -37.48% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.299855 | -27.52% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.542787 | -19.17% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 0 / 69 | 0.413032 | 0.413826 | 0.420032 | 0.299855 | -27.40% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 0 / 24 | 0.479865 | 0.472316 | 0.479303 | 0.326672 | -31.92% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0 / 69 | 0.358721 | 0.359340 | 0.364725 | 0.258643 | -27.90% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0 / 24 | 0.419247 | 0.412473 | 0.418457 | 0.271823 | -35.16% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 0 / 69 | 0.358666 | 0.359601 | 0.365194 | 0.258643 | -27.89% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 0 / 24 | 0.393454 | 0.386399 | 0.392108 | 0.245518 | -37.60% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0 / 69 | 0.364080 | 0.364932 | 0.370969 | 0.262505 | -27.90% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0 / 24 | 0.451672 | 0.445328 | 0.451445 | 0.305542 | -32.35% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 0 / 69 | 0.364444 | 0.364580 | 0.370731 | 0.262505 | -27.97% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 0 / 24 | 0.402906 | 0.396176 | 0.402359 | 0.253015 | -37.20% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
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
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | all | 92 | 4324 | 0.423260 | 0.387808 | 0.278969 | -28.07% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 68 | 3196 | 0.385821 | 0.385597 | 0.274788 | -28.74% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 24 | 1128 | 0.529336 | 0.522342 | 0.385813 | -26.14% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | all | 92 | 4508 | 0.398339 | 0.387570 | 0.276711 | -28.60% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | kda | 68 | 3332 | 0.385744 | 0.385530 | 0.274788 | -28.72% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | mla | 24 | 1176 | 0.434026 | 0.426871 | 0.277757 | -34.93% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | all | 92 | 5428 | 0.332185 | 0.322654 | 0.253455 | -21.45% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 68 | 4012 | 0.320798 | 0.320809 | 0.256849 | -19.94% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 24 | 1416 | 0.364449 | 0.357739 | 0.243374 | -31.97% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | all | 92 | 5428 | 0.329965 | 0.323043 | 0.253455 | -21.54% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | kda | 68 | 4012 | 0.320901 | 0.321012 | 0.256849 | -19.99% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | mla | 24 | 1416 | 0.355645 | 0.348701 | 0.236620 | -32.14% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | all | 92 | 4968 | 0.365059 | 0.354617 | 0.257483 | -27.39% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 68 | 3672 | 0.353110 | 0.352903 | 0.257483 | -27.04% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 24 | 1296 | 0.398913 | 0.391767 | 0.253322 | -35.34% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | all | 92 | 5060 | 0.361328 | 0.354858 | 0.254089 | -28.40% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | kda | 68 | 3740 | 0.353330 | 0.353148 | 0.257483 | -27.09% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | mla | 24 | 1320 | 0.383988 | 0.376723 | 0.239974 | -36.30% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.304390 | -26.80% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.300208 | -27.52% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.542674 | -18.32% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | all | 92 | 4232 | 0.431283 | 0.415334 | 0.304390 | -26.71% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | kda | 68 | 3128 | 0.414137 | 0.414040 | 0.300208 | -27.49% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | mla | 24 | 1104 | 0.479865 | 0.472222 | 0.326559 | -30.85% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | all | 92 | 4784 | 0.375177 | 0.361188 | 0.263217 | -27.12% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 68 | 3536 | 0.359622 | 0.359235 | 0.259035 | -27.89% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 24 | 1248 | 0.419247 | 0.412474 | 0.271711 | -34.13% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | all | 92 | 4876 | 0.368455 | 0.361070 | 0.255641 | -29.20% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | kda | 68 | 3604 | 0.359632 | 0.359552 | 0.259035 | -27.96% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | mla | 24 | 1272 | 0.393454 | 0.386327 | 0.245406 | -36.48% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | all | 92 | 4692 | 0.387800 | 0.367070 | 0.267079 | -27.24% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 68 | 3468 | 0.365257 | 0.364968 | 0.262897 | -27.97% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 24 | 1224 | 0.451672 | 0.445448 | 0.305430 | -31.43% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | all | 92 | 4784 | 0.375068 | 0.366904 | 0.259503 | -29.27% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | kda | 68 | 3536 | 0.365243 | 0.364788 | 0.262897 | -27.93% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | mla | 24 | 1248 | 0.402906 | 0.395987 | 0.252902 | -36.13% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 0.304707 | 0.302280 | 0.304417 | 0.226067 | -25.81% |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 49 | 0.335331 | 0.302283 | 0.304588 | 0.226067 | -32.58% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 0.259493 | 0.258140 | 0.259720 | 0.207326 | -20.10% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 59 | 0.277218 | 0.257813 | 0.259545 | 0.207326 | -25.21% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 0.287557 | 0.269792 | 0.271359 | 0.207960 | -27.68% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 55 | 0.302651 | 0.269840 | 0.271908 | 0.207960 | -31.29% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.253372 | -30.01% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 46 | 0.337916 | 0.337564 | 0.341257 | 0.253372 | -25.02% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 0.297407 | 0.276998 | 0.278997 | 0.209513 | -29.55% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 53 | 0.293014 | 0.277106 | 0.279247 | 0.209513 | -28.50% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 0.284019 | 0.281037 | 0.283397 | 0.213375 | -24.87% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 52 | 0.310159 | 0.281559 | 0.283741 | 0.213375 | -31.20% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
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

Summary: {"case_count": 12, "compared_cases": 12, "failed_cases": 0, "measured_cases": 12, "passed_cases": 0, "source_case_count": 12, "unresolved_cases": 0}
