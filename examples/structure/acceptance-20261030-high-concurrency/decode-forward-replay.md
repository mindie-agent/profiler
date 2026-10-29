# Decode body-forward replay

Existing local captures only. Automatic topology alignment is labelled separately from explicit Host/module boundaries; graph envelopes are separate diagnostics.

Runtime source declaration: {"basis": "caller_identified_installed_package", "source_commit": "bc375e61"}.

Sim 0.8.0; 217 package files; SHA256 `83fab0bfbd15620172a7f323e83c93c661af9aadd9fe7a61fa8a7ebe4e0f9148`; package `/Users/maoxx241/code/sim-rewrite-20261027/.venv/lib/python3.13/site-packages/mindie_sim`.

| Case | Body calls | Real mean ms | P50 ms | P90 ms | Sim ms | Error | Status / reason |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_qwen36_highconc_c40:q4_b40_m160 | 54 | 20.683911 | 20.611527 | 21.333773 | 9.620067 | -53.49% | compared |
| a5_qwen36_highconc_c128:q4_b128_m512 | 38 | 32.608990 | 32.227435 | 33.851394 | 19.987504 | -38.71% | compared |
| a5_qwen36_highconc_c4:q4_b4_m16 | 73 | 13.342454 | 13.244635 | 13.484726 | 5.091275 | -61.84% | compared |
| a5_qwen38_highconc_c32:q4_b32_m128 | 48 | 22.791335 | 22.711011 | 22.894013 | 8.955017 | -60.71% | compared |
| a5_qwen38_highconc_c128:q4_b128_m512 | 29 | 45.689314 | 45.690342 | 45.735162 | 28.248389 | -38.17% | compared |
| a5_qwen38_highconc_c4:q4_b4_m16 | 45 | 13.026721 | 13.005325 | 13.166872 | 4.385865 | -66.33% | compared |

## Device activity and internal uncovered intervals

Device activity is the interval union of retained non-scheduler device events. Real HCOM intervals include protocol wait, so this coverage is not PMU-confirmed useful hardware busy time. Internal uncovered time is body span minus this union. It remains inside body latency and does not by itself identify Host scheduling. Concurrent stream activity is not additive.

Sim assumes symmetric TP peers initially ready at zero. A measured collective interval may include peer wait; single-rank profiling cannot separate payload transport from that wait, so this elapsed time is not a link-bandwidth calibration.

| Case | Real body mean ms | Device activity mean ms | Internal uncovered mean ms | Uncovered fraction | Captured graph mode |
|---|---:|---:|---:|---:|---|
| a5_qwen36_highconc_c40:q4_b40_m160 | 20.683911 | 20.302463 | 0.381448 | 1.84% | FULL_AND_PIECEWISE |
| a5_qwen36_highconc_c128:q4_b128_m512 | 32.608990 | 32.315990 | 0.293001 | 0.90% | FULL_AND_PIECEWISE |
| a5_qwen36_highconc_c4:q4_b4_m16 | 13.342454 | 12.987191 | 0.355263 | 2.66% | FULL_AND_PIECEWISE |
| a5_qwen38_highconc_c32:q4_b32_m128 | 22.791335 | 22.352767 | 0.438568 | 1.92% | FULL_AND_PIECEWISE |
| a5_qwen38_highconc_c128:q4_b128_m512 | 45.689314 | 45.385279 | 0.304035 | 0.67% | FULL_AND_PIECEWISE |
| a5_qwen38_highconc_c4:q4_b4_m16 | 13.026721 | 12.555020 | 0.471701 | 3.62% | FULL_AND_PIECEWISE |

## Per-layer comparison

Dense/MoE labels identify the FFN inside each transformer layer. Statistics below are across measured layer means within the same q/batch group; attention remains part of its declared layer. DP replicas are not summed.

| Case | FFN structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | dense_layer | 0 / 64 | 0.322351 | 0.306924 | 0.310396 | 0.150314 | -53.37% |
| a5_qwen36_highconc_c128:q4_b128_m512 | dense_layer | 0 / 64 | 0.508731 | 0.499688 | 0.501555 | 0.312305 | -38.61% |
| a5_qwen36_highconc_c4:q4_b4_m16 | dense_layer | 0 / 64 | 0.207685 | 0.177630 | 0.182859 | 0.079551 | -61.70% |
| a5_qwen38_highconc_c32:q4_b32_m128 | dense_layer | 0 / 64 | 0.355259 | 0.378954 | 0.385319 | 0.139922 | -60.61% |
| a5_qwen38_highconc_c128:q4_b128_m512 | dense_layer | 0 / 64 | 0.713033 | 0.760891 | 0.763548 | 0.441381 | -38.10% |
| a5_qwen38_highconc_c4:q4_b4_m16 | dense_layer | 0 / 64 | 0.202655 | 0.207141 | 0.208962 | 0.068529 | -66.18% |

## Layers grouped by attention structure

Each value is a complete transformer-layer span, grouped by its declared attention structure; it is not the duration of attention alone. These groups partition the same per-layer comparisons above.

| Case | Attention structure | Layers passed / compared | Real layer mean ms | P50 ms | P90 ms | Sim layer mean ms | Error |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40:q4_b40_m160 | gdn | 0 / 48 | 0.333238 | 0.307781 | 0.311006 | 0.143841 | -56.84% |
| a5_qwen36_highconc_c40:q4_b40_m160 | gqa | 0 / 16 | 0.289689 | 0.289770 | 0.290278 | 0.169731 | -41.41% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gdn | 0 / 48 | 0.515500 | 0.500258 | 0.502235 | 0.308348 | -40.18% |
| a5_qwen36_highconc_c128:q4_b128_m512 | gqa | 0 / 16 | 0.488422 | 0.488369 | 0.490923 | 0.324176 | -33.63% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gdn | 0 / 48 | 0.215818 | 0.177193 | 0.178646 | 0.073557 | -65.92% |
| a5_qwen36_highconc_c4:q4_b4_m16 | gqa | 0 / 16 | 0.183285 | 0.182644 | 0.183628 | 0.097534 | -46.79% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gdn | 0 / 48 | 0.381152 | 0.381610 | 0.385877 | 0.148881 | -60.94% |
| a5_qwen38_highconc_c32:q4_b32_m128 | gqa | 0 / 16 | 0.277580 | 0.274090 | 0.275037 | 0.113047 | -59.27% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gdn | 0 / 48 | 0.761777 | 0.761850 | 0.763812 | 0.473718 | -37.81% |
| a5_qwen38_highconc_c128:q4_b128_m512 | gqa | 0 / 16 | 0.566802 | 0.566580 | 0.568505 | 0.344371 | -39.24% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gdn | 0 / 48 | 0.207698 | 0.207635 | 0.209199 | 0.064610 | -68.89% |
| a5_qwen38_highconc_c4:q4_b4_m16 | gqa | 0 / 16 | 0.187527 | 0.181657 | 0.181965 | 0.080287 | -57.19% |

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
