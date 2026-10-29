# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_selected_package", "source_commit": "aeb66892a20588825e0eb443894d5d9b6b71c641"}.

Variant: `kimi-logical96-p16k`. Baseline: null.

Sim 0.8.0; 246 package files; SHA256 `7f30d18bcf75f1f4974fb9a1cc4301d063636f7156431ad4f93019b5e3a70200`; package `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 39.247386 | 39.244948 | 39.262920 | 27.154800 | -30.81% | compared |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 30.823435 | 30.822007 | 30.838985 | 23.049787 | -25.22% | compared |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 33.875753 | 33.857996 | 33.873078 | 23.272186 | -31.30% | compared |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 44.666193 | 44.645272 | 44.661803 | 32.304070 | -27.68% | compared |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 34.816498 | 34.793753 | 34.812948 | 23.716984 | -31.88% | compared |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 35.964417 | 35.962094 | 35.978788 | 24.605270 | -31.58% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode | Sim TP / DP / EP | Sim graph mode / capture |
|---|---:|---:|---:|---:|---|---|---|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247386 | 38.566577 | 0.680809 | 1.73% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823435 | 30.183881 | 0.639554 | 2.07% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.875753 | 33.190409 | 0.685344 | 2.02% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666193 | 43.970836 | 0.695357 | 1.56% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816498 | 34.115094 | 0.701404 | 2.01% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964417 | 35.281594 | 0.682823 | 1.90% | FULL_DECODE_ONLY launch intent; simulated graph wrapper omitted at this body boundary | 8 / 1 / 8 | eager / full |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | dense_layer | 0 / 1 | 0.304707 | 0.304707 | 0.304707 | 0.245133 | -19.55% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | moe_layer | 0 / 92 | 0.423260 | 0.387824 | 0.524838 | 0.292354 | -30.93% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | dense_layer | 0 / 1 | 0.259493 | 0.259493 | 0.259493 | 0.211561 | -18.47% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | moe_layer | 0 / 92 | 0.332185 | 0.322766 | 0.359609 | 0.248088 | -25.32% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | dense_layer | 0 / 1 | 0.287557 | 0.287557 | 0.287557 | 0.213139 | -25.88% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | moe_layer | 0 / 92 | 0.365059 | 0.354655 | 0.392704 | 0.250488 | -31.38% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | dense_layer | 0 / 1 | 0.362005 | 0.362005 | 0.362005 | 0.290186 | -19.84% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | moe_layer | 0 / 92 | 0.481537 | 0.416109 | 0.665712 | 0.347829 | -27.77% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | dense_layer | 0 / 1 | 0.297407 | 0.297407 | 0.297407 | 0.216295 | -27.27% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | moe_layer | 0 / 92 | 0.375177 | 0.361169 | 0.412914 | 0.255288 | -31.96% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | dense_layer | 0 / 1 | 0.284019 | 0.284019 | 0.284019 | 0.222607 | -21.62% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | moe_layer | 0 / 92 | 0.387800 | 0.367269 | 0.446146 | 0.264889 | -31.69% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0 / 69 | 0.384646 | 0.385628 | 0.391398 | 0.286027 | -25.64% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0 / 24 | 0.529336 | 0.522407 | 0.529076 | 0.308576 | -41.71% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0 / 69 | 0.319910 | 0.320784 | 0.326143 | 0.253469 | -20.77% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0 / 24 | 0.364449 | 0.357714 | 0.364380 | 0.231093 | -36.59% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0 / 69 | 0.352160 | 0.352714 | 0.358215 | 0.255047 | -27.58% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0 / 24 | 0.398913 | 0.391929 | 0.399012 | 0.235823 | -40.88% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0 / 69 | 0.413723 | 0.414344 | 0.421089 | 0.329588 | -20.34% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0 / 24 | 0.671523 | 0.664634 | 0.670936 | 0.397869 | -40.75% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0 / 69 | 0.358721 | 0.359340 | 0.364725 | 0.258203 | -28.02% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0 / 24 | 0.419247 | 0.412473 | 0.418457 | 0.245282 | -41.49% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0 / 69 | 0.364080 | 0.364932 | 0.370969 | 0.264515 | -27.35% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0 / 24 | 0.451672 | 0.445328 | 0.451445 | 0.264202 | -41.51% |

| Case | Attention structure | Complete layer mean ms | Layer device activity mean ms | Layer internal uncovered mean ms |
|---|---|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 0.384646 | 0.379054 | 0.005591 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 0.529336 | 0.517159 | 0.012177 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 0.319910 | 0.314950 | 0.004960 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 0.364449 | 0.352180 | 0.012269 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 0.352160 | 0.346560 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 0.398913 | 0.386575 | 0.012338 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 0.413723 | 0.407971 | 0.005752 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 0.671523 | 0.659202 | 0.012321 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 0.358721 | 0.352935 | 0.005785 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 0.419247 | 0.406773 | 0.012474 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 0.364080 | 0.358480 | 0.005600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 0.451672 | 0.439438 | 0.012234 |

## Steady layer statistics excluding Layer 0

The body and complete-layer Mean errors above retain Layer 0. Here each layer's P50 uses all its Forward calls, then the table takes the median across those layer P50s. This is not a pooled P50 over all layer invocations. Sim uses the median of the same declared layer predictions. The call count describes the retained population, not a claim that its pooled quantile was computed.

| Case | Attention group | Layers | Layer calls | Real layer mean ms | Median of layer-call P50 ms | Sim layer median ms | P50 comparison error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | all | 92 | 4324 | 0.423260 | 0.387808 | 0.290480 | -25.10% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | kda | 68 | 3196 | 0.385821 | 0.385597 | 0.286298 | -25.75% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | mla | 24 | 1128 | 0.529336 | 0.522342 | 0.308463 | -40.95% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | all | 92 | 5428 | 0.332185 | 0.322654 | 0.250361 | -22.41% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | kda | 68 | 4012 | 0.320798 | 0.320809 | 0.253755 | -20.90% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | mla | 24 | 1416 | 0.364449 | 0.357739 | 0.230980 | -35.43% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | all | 92 | 4968 | 0.365059 | 0.354617 | 0.251939 | -28.95% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | kda | 68 | 3672 | 0.353110 | 0.352903 | 0.255333 | -27.65% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | mla | 24 | 1296 | 0.398913 | 0.391767 | 0.235710 | -39.83% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | all | 92 | 3772 | 0.481537 | 0.415844 | 0.334019 | -19.68% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | kda | 68 | 2788 | 0.414483 | 0.414203 | 0.329837 | -20.37% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | mla | 24 | 984 | 0.671523 | 0.664380 | 0.397756 | -40.13% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | all | 92 | 4784 | 0.375177 | 0.361188 | 0.255095 | -29.37% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | kda | 68 | 3536 | 0.359622 | 0.359235 | 0.258489 | -28.04% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | mla | 24 | 1248 | 0.419247 | 0.412474 | 0.245170 | -40.56% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | all | 92 | 4692 | 0.387800 | 0.367070 | 0.264801 | -27.86% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | kda | 68 | 3468 | 0.365257 | 0.364968 | 0.264801 | -27.45% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | mla | 24 | 1224 | 0.451672 | 0.445448 | 0.264089 | -40.71% |

Layer 0 remains in body latency and the complete-layer comparison:

| Case | Layer 0 calls | Real mean ms | P50 ms | P90 ms | Sim ms | Mean error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 47 | 0.304707 | 0.302280 | 0.304417 | 0.245133 | -19.55% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 59 | 0.259493 | 0.258140 | 0.259720 | 0.211561 | -18.47% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 54 | 0.287557 | 0.269792 | 0.271359 | 0.213139 | -25.88% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 41 | 0.362005 | 0.338372 | 0.341159 | 0.290186 | -19.84% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 52 | 0.297407 | 0.276998 | 0.278997 | 0.216295 | -27.27% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 51 | 0.284019 | 0.281037 | 0.283397 | 0.222607 | -21.62% |

## Execution batch and client TPOT

Execution batch comes from captured tensor geometry and may include graph padding. Client concurrency describes requests. Representative K is the explicitly declared context or client prompt length; generated-token growth during the window is not observed. These single-rank comparisons assume symmetric rank completion. TPOT includes serving work beyond the body; profiled and unprofiled measurements remain separate.

| Case | Executed q | Executed batch | Query rows | Valid active rows | Representative K | Client concurrency | Profiled client TPOT mean ms | Profiled client TPOT P50 ms | Profiled window TPOT estimate ms | Unprofiled sweep TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 1 | 16 | 16 | unknown | 16392 | 16 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 1 | 1 | 1 | unknown | 16392 | 1 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 1 | 2 | 2 | unknown | 16392 | 2 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 1 | 32 | 32 | unknown | 16392 | 32 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 1 | 4 | 4 | unknown | 16392 | 4 | — | — | — | — |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 1 | 8 | 8 | unknown | 16392 | 8 | — | — | — | — |

## Separate model boundaries

These measured scopes are outside the target body comparison. Unavailable scopes have no numeric row; a missing scope is not zero cost. The original stage kind is retained, including ambiguous auxiliary/MTP labels.

| Case | Boundary | Observed calls | Mean ms | P50 ms | P90 ms |
|---|---|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | embedding | 47 | 0.004621 | 0.004452 | 0.005158 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | final_norm | 47 | 0.004149 | 0.004128 | 0.004346 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | lm_head | 47 | 0.092373 | 0.092297 | 0.093138 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | embedding | 59 | 0.003153 | 0.003145 | 0.003345 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | final_norm | 59 | 0.002648 | 0.002644 | 0.002801 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | lm_head | 59 | 0.090694 | 0.090708 | 0.091441 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | embedding | 54 | 0.003248 | 0.003227 | 0.003438 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | final_norm | 54 | 0.003575 | 0.003547 | 0.003697 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | lm_head | 54 | 0.090737 | 0.090634 | 0.091393 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | embedding | 41 | 0.003452 | 0.003466 | 0.003683 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | final_norm | 41 | 0.005865 | 0.005876 | 0.006045 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | lm_head | 41 | 0.117608 | 0.117655 | 0.118201 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | embedding | 52 | 0.004307 | 0.004195 | 0.004880 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | final_norm | 52 | 0.003656 | 0.003638 | 0.003791 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | lm_head | 52 | 0.091122 | 0.090941 | 0.091927 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | embedding | 51 | 0.004301 | 0.004254 | 0.004600 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | final_norm | 51 | 0.003739 | 0.003723 | 0.003842 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | lm_head | 51 | 0.091241 | 0.091220 | 0.091749 |

Summary: {"case_count": 6, "compared_cases": 6, "failed_cases": 0, "measured_cases": 6, "passed_cases": 0, "source_case_count": 6, "unresolved_cases": 0}
