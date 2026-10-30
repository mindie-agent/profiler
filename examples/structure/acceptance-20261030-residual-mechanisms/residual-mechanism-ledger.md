# Residual mechanism ledger — fixed 9f10558 baseline

38 distinct captures / 2796 selected complete Body forwards. No raw re-scan or new prediction.

Four clusters retain complete native-family measurements and individual strict/reference provenance. **The millisecond columns are nonadditive activity residuals, not a causal Body budget. Do not sum clusters.** Missing costs are shown as `—`; partial references never extrapolate to an entire native family.

A3 includes the requested V4Flash c4 and Kimi4 c32, then the two remaining failed sources closest to the ±15% relative band. Absolute milliseconds are shown separately; small four-layer absolute gaps do not imply relative accuracy. The full eligible ranking is retained in JSON.

## Model-group mechanism ranges

Ranges describe separate case populations. Covered Real/Sim/residual use the same covered calls within each case; rows with no cost do not enter those ranges. Inactive clusters are omitted here and retained in JSON.

| Model group / cluster | Measured / cost-covered cases | All Real ms/F range | Covered Real / Sim ms/F ranges | Covered residual ms/F range | Strict / reference / uncovered calls |
|---|---:|---:|---:|---:|---:|
| A5 Qwen3.5 TP4 (3) / A | 3 / 0 of 3 | 1.157–3.372 | — / — | — | 0 / 0 / 19120 |
| A5 Qwen3.5 TP4 (3) / C | 3 / 0 of 3 | 2.530–6.470 | — / — | — | 0 / 0 / 28680 |
| A5 Qwen3.5 TP4 (3) / D | 3 / 0 of 3 | 2.536–4.987 | — / — | — | 0 / 0 / 28680 |
| A5 GLM Flash failed (9) / B | 9 / 3 of 9 | 1.124–2.689 | 1.533–2.689 / 0.144–0.227 | -2.462–-1.389 | 3864 / 6256 / 24860 |
| A5 GLM Flash failed (9) / C | 9 / 9 of 9 | 2.352–13.728 | 2.352–13.728 / 1.247–11.747 | -1.982–-1.105 | 13356 / 13356 / 0 |
| A5 GLM Flash failed (9) / D | 9 / 0 of 9 | 1.974–3.839 | — / — | — | 0 / 0 / 28620 |
| A5 Kimi BF16 (12) / A | 12 / 12 of 12 | 4.220–6.086 | 4.220–6.086 / 0.582–0.670 | -5.504–-3.638 | 0 / 113712 / 0 |
| A5 Kimi BF16 (12) / C | 12 / 12 of 12 | 3.493–6.279 | 3.493–6.279 / 3.848–4.045 | -2.234–0.356 | 0 / 113712 / 0 |
| A5 Kimi BF16 (12) / D | 12 / 0 of 12 | 4.213–5.113 | — / — | — | 0 / 0 / 230514 |
| A5 Qwen3.6 TP2 (3) / D | 3 / 3 of 3 | 1.387–16.614 | 1.387–16.614 / 0.528–10.200 | -6.414–-0.177 | 0 / 20992 / 0 |
| A5 V4.1 (7) / A | 7 / 7 of 7 | 1.188–2.361 | 1.188–2.361 / 0.277–0.462 | -2.084–-0.896 | 0 / 66400 / 0 |
| A5 V4.1 (7) / C | 7 / 7 of 7 | 2.488–14.937 | 2.488–14.937 / 1.616–12.961 | -1.976–-0.872 | 0 / 66400 / 0 |
| A3 nearest failed boundary (4) / A | 4 / 0 of 4 | 0.224–5.389 | — / — | — | 0 / 0 / 19138 |
| A3 nearest failed boundary (4) / C | 2 / 2 of 4 | 0.283–2.805 | 0.283–2.805 / 0.794–3.102 | 0.296–0.511 | 0 / 2844 / 0 |
| A3 nearest failed boundary (4) / D | 4 / 1 of 4 | 0.750–9.497 | 0.693–0.693 / 0.074–0.074 | -0.619–-0.619 | 0 / 3300 / 29493 |

## Per-case clusters

| Case | Body Real / Sim ms | ms to 15% band | Cluster | All observed ms/F | Covered Real / Sim ms/F | Strict / reference / uncovered calls (per F) | Covered activity residual ms/F |
|---|---:|---:|---|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.585 / 14.845 | 9.452 | A | 3.372 | — / — | 0 / 0 / 6080 (0.00 / 0.00 / 80.00) | — |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.585 / 14.845 | 9.452 | C | 6.470 | — / — | 0 / 0 / 9120 (0.00 / 0.00 / 120.00) | — |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.585 / 14.845 | 9.452 | D | 4.987 | — / — | 0 / 0 / 9120 (0.00 / 0.00 / 120.00) | — |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.616 / 20.322 | 8.252 | B | 1.513 | — / — | 0 / 0 / 3520 (0.00 / 0.00 / 110.00) | — |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.616 / 20.322 | 8.252 | C | 12.971 | 12.971 / 11.261 | 1344 / 1344 / 0 (42.00 / 42.00 / 0.00) | -1.710 |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.616 / 20.322 | 8.252 | D | 3.090 | — / — | 0 / 0 / 2880 (0.00 / 0.00 / 90.00) | — |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.713 / 25.491 | 7.416 | B | 1.897 | — / — | 0 / 0 / 3850 (0.00 / 0.00 / 110.00) | — |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.713 / 25.491 | 7.416 | C | 13.343 | 13.343 / 11.423 | 1470 / 1470 / 0 (42.00 / 42.00 / 0.00) | -1.920 |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.713 / 25.491 | 7.416 | D | 3.254 | — / — | 0 / 0 / 3150 (0.00 / 0.00 / 90.00) | — |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.031 / 20.135 | 7.942 | B | 1.533 | 1.533 / 0.144 | 1260 / 2040 / 0 (42.00 / 68.00 / 0.00) | -1.389 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.031 / 20.135 | 7.942 | C | 12.992 | 12.992 / 11.261 | 1260 / 1260 / 0 (42.00 / 42.00 / 0.00) | -1.731 |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.031 / 20.135 | 7.942 | D | 3.097 | — / — | 0 / 0 / 2700 (0.00 / 0.00 / 90.00) | — |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.669 / 25.111 | 6.907 | B | 1.914 | 1.914 / 0.163 | 1302 / 2108 / 0 (42.00 / 68.00 / 0.00) | -1.751 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.669 / 25.111 | 6.907 | C | 13.343 | 13.343 / 11.423 | 1302 / 1302 / 0 (42.00 / 42.00 / 0.00) | -1.920 |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.669 / 25.111 | 6.907 | D | 3.265 | — / — | 0 / 0 / 2790 (0.00 / 0.00 / 90.00) | — |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833 / 16.619 | 7.889 | B | 1.305 | — / — | 0 / 0 / 3300 (0.00 / 0.00 / 110.00) | — |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833 / 16.619 | 7.889 | C | 11.583 | 11.583 / 9.952 | 1260 / 1260 / 0 (42.00 / 42.00 / 0.00) | -1.631 |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.833 / 16.619 | 7.889 | D | 2.544 | — / — | 0 / 0 / 2700 (0.00 / 0.00 / 90.00) | — |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528 / 34.519 | 5.030 | B | 2.689 | 2.689 / 0.227 | 1302 / 2108 / 0 (42.00 / 68.00 / 0.00) | -2.462 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528 / 34.519 | 5.030 | C | 13.728 | 13.728 / 11.747 | 1302 / 1302 / 0 (42.00 / 42.00 / 0.00) | -1.982 |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.528 / 34.519 | 5.030 | D | 3.839 | — / — | 0 / 0 / 2790 (0.00 / 0.00 / 90.00) | — |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.019 / 28.544 | 5.472 | A | 4.488 | 4.488 / 0.670 | 0 / 8464 / 0 (0.00 / 184.00 / 0.00) | -3.817 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.019 / 28.544 | 5.472 | C | 6.279 | 6.279 / 4.045 | 0 / 8464 / 0 (0.00 / 184.00 / 0.00) | -2.234 |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.019 / 28.544 | 5.472 | D | 5.017 | — / — | 0 / 0 / 17158 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985 / 25.616 | 5.821 | A | 4.429 | 4.429 / 0.620 | 0 / 9016 / 0 (0.00 / 184.00 / 0.00) | -3.809 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985 / 25.616 | 5.821 | C | 6.007 | 6.007 / 3.914 | 0 / 9016 / 0 (0.00 / 184.00 / 0.00) | -2.093 |
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.985 / 25.616 | 5.821 | D | 4.765 | — / — | 0 / 0 / 18277 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247 / 28.209 | 5.151 | A | 4.426 | 4.426 / 0.620 | 0 / 8648 / 0 (0.00 / 184.00 / 0.00) | -3.806 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247 / 28.209 | 5.151 | C | 6.012 | 6.012 / 3.914 | 0 / 8648 / 0 (0.00 / 184.00 / 0.00) | -2.098 |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.247 / 28.209 | 5.151 | D | 4.751 | — / — | 0 / 0 / 17531 (0.00 / 0.00 / 373.00) | — |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.957 / 10.942 | 7.722 | A | 2.247 | — / — | 0 / 0 / 6320 (0.00 / 0.00 / 80.00) | — |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.957 / 10.942 | 7.722 | C | 6.269 | — / — | 0 / 0 / 9480 (0.00 / 0.00 / 120.00) | — |
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.957 / 10.942 | 7.722 | D | 3.855 | — / — | 0 / 0 / 9480 (0.00 / 0.00 / 120.00) | — |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666 / 33.731 | 4.236 | A | 4.492 | 4.492 / 0.670 | 0 / 7544 / 0 (0.00 / 184.00 / 0.00) | -3.821 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666 / 33.731 | 4.236 | C | 6.277 | 6.277 / 4.045 | 0 / 7544 / 0 (0.00 / 184.00 / 0.00) | -2.232 |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.666 / 33.731 | 4.236 | D | 5.113 | — / — | 0 / 0 / 15293 (0.00 / 0.00 / 373.00) | — |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418 / 10.681 | 7.525 | B | 1.224 | — / — | 0 / 0 / 1210 (0.00 / 0.00 / 110.00) | — |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418 / 10.681 | 7.525 | C | 6.296 | 6.296 / 4.977 | 462 / 462 / 0 (42.00 / 42.00 / 0.00) | -1.318 |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.418 / 10.681 | 7.525 | D | 2.062 | — / — | 0 / 0 / 990 (0.00 / 0.00 / 90.00) | — |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819 / 24.198 | 5.398 | A | 4.363 | 4.363 / 0.582 | 0 / 9568 / 0 (0.00 / 184.00 / 0.00) | -3.781 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819 / 24.198 | 5.398 | C | 5.817 | 5.817 / 3.848 | 0 / 9568 / 0 (0.00 / 184.00 / 0.00) | -1.968 |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.819 / 24.198 | 5.398 | D | 4.606 | — / — | 0 / 0 / 19396 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964 / 25.459 | 5.111 | A | 4.368 | 4.368 / 0.582 | 0 / 9384 / 0 (0.00 / 184.00 / 0.00) | -3.786 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964 / 25.459 | 5.111 | C | 5.819 | 5.819 / 3.848 | 0 / 9384 / 0 (0.00 / 184.00 / 0.00) | -1.971 |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.964 / 25.459 | 5.111 | D | 4.565 | — / — | 0 / 0 / 19023 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.194 / 23.753 | 5.312 | A | 4.259 | 4.259 / 0.582 | 0 / 9752 / 0 (0.00 / 184.00 / 0.00) | -3.677 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.194 / 23.753 | 5.312 | C | 5.640 | 5.640 / 3.848 | 0 / 9752 / 0 (0.00 / 184.00 / 0.00) | -1.792 |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.194 / 23.753 | 5.312 | D | 4.424 | — / — | 0 / 0 / 19769 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816 / 24.384 | 5.210 | A | 4.251 | 4.251 / 0.582 | 0 / 9568 / 0 (0.00 / 184.00 / 0.00) | -3.669 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816 / 24.384 | 5.210 | C | 5.664 | 5.664 / 3.848 | 0 / 9568 / 0 (0.00 / 184.00 / 0.00) | -1.816 |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.816 / 24.384 | 5.210 | D | 4.436 | — / — | 0 / 0 / 19396 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.876 / 23.836 | 4.959 | A | 6.086 | 6.086 / 0.582 | 0 / 9936 / 0 (0.00 / 184.00 / 0.00) | -5.504 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.876 / 23.836 | 4.959 | C | 3.547 | 3.547 / 3.848 | 0 / 9936 / 0 (0.00 / 184.00 / 0.00) | 0.301 |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.876 / 23.836 | 4.959 | D | 4.458 | — / — | 0 / 0 / 20142 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.548 / 23.515 | 5.000 | A | 6.075 | 6.075 / 0.582 | 0 / 10120 / 0 (0.00 / 184.00 / 0.00) | -5.493 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.548 / 23.515 | 5.000 | C | 3.556 | 3.556 / 3.848 | 0 / 10120 / 0 (0.00 / 184.00 / 0.00) | 0.293 |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.548 / 23.515 | 5.000 | D | 4.463 | — / — | 0 / 0 / 20515 (0.00 / 0.00 / 373.00) | — |
| qwen36-a5-tp2-c96:q4_b96_m384 | 63.853 / 53.947 | 0.328 | D | 16.614 | 16.614 / 10.200 | 0 / 3072 / 0 (0.00 / 128.00 / 0.00) | -6.414 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.068 / 11.803 | 6.105 | B | 1.161 | — / — | 0 / 0 / 5830 (0.00 / 0.00 / 110.00) | — |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.068 / 11.803 | 6.105 | C | 6.311 | 6.311 / 4.977 | 2226 / 2226 / 0 (42.00 / 42.00 / 0.00) | -1.333 |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.068 / 11.803 | 6.105 | D | 2.226 | — / — | 0 / 0 / 4770 (0.00 / 0.00 / 90.00) | — |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683 / 6.830 | 6.501 | B | 1.124 | — / — | 0 / 0 / 7150 (0.00 / 0.00 / 110.00) | — |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683 / 6.830 | 6.501 | C | 2.352 | 2.352 / 1.247 | 2730 / 2730 / 0 (42.00 / 42.00 / 0.00) | -1.105 |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.683 / 6.830 | 6.501 | D | 1.974 | — / — | 0 / 0 / 5850 (0.00 / 0.00 / 90.00) | — |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.286 / 19.245 | 3.948 | A | 1.458 | 1.458 / 0.462 | 0 / 5840 / 0 (0.00 / 80.00 / 0.00) | -0.996 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.286 / 19.245 | 3.948 | C | 14.937 | 14.937 / 12.961 | 0 / 5840 / 0 (0.00 / 80.00 / 0.00) | -1.976 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328 / 18.933 | 3.446 | A | 1.560 | 1.560 / 0.349 | 0 / 6000 / 0 (0.00 / 80.00 / 0.00) | -1.211 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.328 / 18.933 | 3.446 | C | 14.498 | 14.498 / 12.925 | 0 / 6000 / 0 (0.00 / 80.00 / 0.00) | -1.573 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823 / 23.553 | 2.647 | A | 4.220 | 4.220 / 0.582 | 0 / 10856 / 0 (0.00 / 184.00 / 0.00) | -3.638 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823 / 23.553 | 2.647 | C | 3.497 | 3.497 / 3.848 | 0 / 10856 / 0 (0.00 / 184.00 / 0.00) | 0.352 |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.823 / 23.553 | 2.647 | D | 4.213 | — / — | 0 / 0 / 22007 (0.00 / 0.00 / 373.00) | — |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.637 / 23.391 | 2.650 | A | 4.221 | 4.221 / 0.582 | 0 / 10856 / 0 (0.00 / 184.00 / 0.00) | -3.639 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.637 / 23.391 | 2.650 | C | 3.493 | 3.493 / 3.848 | 0 / 10856 / 0 (0.00 / 184.00 / 0.00) | 0.356 |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.637 / 23.391 | 2.650 | D | 4.231 | — / — | 0 / 0 / 22007 (0.00 / 0.00 / 373.00) | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.625 / 12.361 | 3.470 | A | 1.237 | 1.237 / 0.312 | 0 / 8400 / 0 (0.00 / 80.00 / 0.00) | -0.926 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.625 / 12.361 | 3.470 | C | 7.706 | 7.706 / 6.463 | 0 / 8400 / 0 (0.00 / 80.00 / 0.00) | -1.243 |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.551 / 5.368 | 4.451 | A | 1.157 | — / — | 0 / 0 / 6720 (0.00 / 0.00 / 80.00) | — |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.551 / 5.368 | 4.451 | C | 2.530 | — / — | 0 / 0 / 10080 (0.00 / 0.00 / 120.00) | — |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.551 / 5.368 | 4.451 | D | 2.536 | — / — | 0 / 0 / 10080 (0.00 / 0.00 / 120.00) | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.292 / 7.430 | 3.868 | A | 1.626 | 1.626 / 0.277 | 0 / 11600 / 0 (0.00 / 80.00 / 0.00) | -1.350 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.292 / 7.430 | 3.868 | C | 2.488 | 2.488 / 1.616 | 0 / 11600 / 0 (0.00 / 80.00 / 0.00) | -0.872 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929 / 9.078 | 3.612 | A | 1.188 | 1.188 / 0.293 | 0 / 10320 / 0 (0.00 / 80.00 / 0.00) | -0.896 |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.929 / 9.078 | 3.612 | C | 4.221 | 4.221 / 3.232 | 0 / 10320 / 0 (0.00 / 80.00 / 0.00) | -0.989 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.239 / 7.430 | 3.823 | A | 2.361 | 2.361 / 0.277 | 0 / 12080 / 0 (0.00 / 80.00 / 0.00) | -2.084 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.239 / 7.430 | 3.823 | C | 2.496 | 2.496 / 1.616 | 0 / 12080 / 0 (0.00 / 80.00 / 0.00) | -0.881 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.135 / 7.430 | 3.734 | A | 2.261 | 2.261 / 0.277 | 0 / 12160 / 0 (0.00 / 80.00 / 0.00) | -1.985 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.135 / 7.430 | 3.734 | C | 2.489 | 2.489 / 1.616 | 0 / 12160 / 0 (0.00 / 80.00 / 0.00) | -0.873 |
| qwen36-a5-tp2-c12:q4_b12_m48 | 24.226 / 18.850 | 1.742 | D | 5.607 | 5.607 / 5.430 | 0 / 7040 / 0 (0.00 / 128.00 / 0.00) | -0.177 |
| qwen36-a5-tp2-c1:q4_b1_m4 | 12.318 / 7.726 | 2.744 | D | 1.387 | 1.387 / 0.528 | 0 / 10880 / 0 (0.00 / 128.00 / 0.00) | -0.858 |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.486 / 26.525 | 1.088 | A | 2.661 | — / — | 0 / 0 / 8944 (0.00 / 0.00 / 86.00) | — |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.486 / 26.525 | 1.088 | B | — | — / — | 0 / 0 / — (0.00 / 0.00 / —) | — |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.486 / 26.525 | 1.088 | C | — | — / — | 0 / 0 / — (0.00 / 0.00 / —) | — |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.486 / 26.525 | 1.088 | D | 3.138 | — / — | 0 / 0 / 13416 (0.00 / 0.00 / 129.00) | — |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.714 / 5.349 | 0.358 | A | 0.301 | — / — | 0 / 0 / 1320 (0.00 / 0.00 / 6.00) | — |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.714 / 5.349 | 0.358 | C | 2.805 | 2.805 / 3.102 | 0 / 1320 / 0 (0.00 / 6.00 / 0.00) | 0.296 |
| a3_kimi4_tp8_w4a8_c32:q1_b32_m32 | 6.714 / 5.349 | 0.358 | D | 0.750 | 0.693 / 0.074 | 0 / 3300 / 440 (0.00 / 15.00 / 2.00) | -0.619 |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556 / 55.529 | 3.594 | A | 5.389 | — / — | 0 / 0 / 7350 (0.00 / 0.00 / 150.00) | — |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556 / 55.529 | 3.594 | B | — | — / — | 0 / 0 / — (0.00 / 0.00 / —) | — |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556 / 55.529 | 3.594 | C | — | — / — | 0 / 0 / — (0.00 / 0.00 / —) | — |
| a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48 | 69.556 / 55.529 | 3.594 | D | 9.497 | — / — | 0 / 0 / 11319 (0.00 / 0.00 / 231.00) | — |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180 / 2.528 | 0.175 | A | 0.224 | — / — | 0 / 0 / 1524 (0.00 / 0.00 / 6.00) | — |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180 / 2.528 | 0.175 | C | 0.283 | 0.283 / 0.794 | 0 / 1524 / 0 (0.00 / 6.00 / 0.00) | 0.511 |
| a3_kimi4_tp8_w4a8_c1:q1_b1_m1 | 3.180 / 2.528 | 0.175 | D | 0.950 | — / — | 0 / 0 / 4318 (0.00 / 0.00 / 17.00) | — |

## qwen35-35b-a5-tp4-c128-graph:q4_b128_m512

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / DequantSwigluQuant | 40.00 | 56.560 / 56.844 | 0 / 0 | — | — | measured_cost_unavailable |
| C / GroupedMatmul | 80.00 | 52.598 / 54.684 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeCombineV3 | 40.00 | 43.109 / 43.058 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV3 | 40.00 | 41.178 / 41.103 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 40.00 | 30.174 / 30.088 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_ | 80.00 | 47.247 / 46.254 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|

## a5_glm53flash_tp8_c16_p8k:q4_b16_m64

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 102.724 / 102.578 | 1344 / 0 | 4.392 | 0.077 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 206.105 / 205.956 | 0 / 1344 | 6.869 | -1.787 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 22.800 / 22.881 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 8.170 / 8.200 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 34.330 / 32.352 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 102.724 / 102.578 | 104.565 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 205.999 / 205.726 | 163.550 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 206.404 / 206.335 | 163.550 | `6ddf7aa8516c` | conditional_reference |

## a5_glm53flash_tp8_c32_p8k:q4_b32_m128

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 109.853 / 110.481 | 1470 / 0 | 4.485 | -0.129 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 207.849 / 207.460 | 0 / 1470 | 6.939 | -1.791 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 24.737 / 24.852 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 12.624 / 12.438 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 36.152 / 33.578 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 109.853 / 110.481 | 106.775 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 208.272 / 207.963 | 165.203 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 207.698 / 207.331 | 165.203 | `6ddf7aa8516c` | conditional_reference |

## a5_glm53flash_tp8_c16_p4k:q4_b16_m64

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 103.104 / 102.832 | 1260 / 0 | 4.392 | 0.061 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 206.227 / 205.998 | 0 / 1260 | 6.869 | -1.792 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 23.011 / 23.052 | 1260 / 0 | 0.055 | -0.911 | complete_cost_coverage |
| B / _copy_conv_state_kernel | 68.00 | 8.339 / 8.284 | 0 / 2040 | 0.089 | -0.478 | complete_cost_coverage |
| D / hcom_allReduce_AicpuKernel | 90.00 | 34.413 / 32.355 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 103.104 / 102.832 | 104.565 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 206.079 / 205.812 | 163.550 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 206.645 / 206.287 | 163.550 | `6ddf7aa8516c` | conditional_reference |
| MoeInitRoutingV3 / pack | 42.00 | 23.011 / 23.052 | 1.312 | `d5345a2d23c0` | strict_cohort |
| _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 8.339 / 8.284 | 1.312 | `d5345a2d23c0` | conditional_reference |

## a5_glm53flash_tp8_c32_p4k:q4_b32_m128

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 109.824 / 110.412 | 1302 / 0 | 4.485 | -0.128 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 207.865 / 207.616 | 0 / 1302 | 6.939 | -1.792 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 24.685 / 24.843 | 1302 / 0 | 0.074 | -0.963 | complete_cost_coverage |
| B / _copy_conv_state_kernel | 68.00 | 12.896 / 12.476 | 0 / 2108 | 0.089 | -0.788 | complete_cost_coverage |
| D / hcom_allReduce_AicpuKernel | 90.00 | 36.277 / 33.661 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 109.824 / 110.412 | 106.775 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 208.275 / 208.143 | 165.203 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 207.720 / 207.499 | 165.203 | `6ddf7aa8516c` | conditional_reference |
| MoeInitRoutingV3 / pack | 42.00 | 24.685 / 24.843 | 1.756 | `d5345a2d23c0` | strict_cohort |
| _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 12.896 / 12.476 | 1.312 | `d5345a2d23c0` | conditional_reference |

## a5_glm53flash_tp8_c8_p4k:q4_b8_m32

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 91.186 / 90.988 | 1260 / 0 | 3.868 | 0.038 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 184.592 / 184.147 | 0 / 1260 | 6.084 | -1.669 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 21.641 / 21.509 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 5.823 / 5.816 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 28.268 / 24.293 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 91.186 / 90.988 | 92.089 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 184.394 / 183.976 | 144.860 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 185.150 / 184.762 | 144.860 | `6ddf7aa8516c` | conditional_reference |

## a5_glm53flash_tp8_c64_p4k:q4_b64_m256

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 115.777 / 117.337 | 1302 / 0 | 4.670 | -0.192 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 211.089 / 210.722 | 0 / 1302 | 7.076 | -1.789 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 28.768 / 28.822 | 1302 / 0 | 0.138 | -1.071 | complete_cost_coverage |
| B / _copy_conv_state_kernel | 68.00 | 21.777 / 21.506 | 0 / 2108 | 0.089 | -1.392 | complete_cost_coverage |
| D / hcom_allReduce_AicpuKernel | 90.00 | 42.658 / 40.072 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 115.777 / 117.337 | 111.195 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 211.180 / 210.918 | 168.484 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 210.831 / 210.350 | 168.484 | `6ddf7aa8516c` | conditional_reference |
| MoeInitRoutingV3 / pack | 42.00 | 28.768 / 28.822 | 3.275 | `d5345a2d23c0` | strict_cohort |
| _copy_conv_state_kernel / conv_state_copy_gather_scatter_cohort | 68.00 | 21.777 / 21.506 | 1.312 | `d5345a2d23c0` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 34.127 / 33.970 | 0 / 8464 | 4.045 | -2.234 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.584 / 14.442 | 0 / 4232 | 0.419 | -0.922 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 34.197 / 34.183 | 0 / 4232 | 0.251 | -2.895 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.737 / 10.701 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 16.176 / 15.850 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 22.016 / 22.110 | 13.086 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 46.237 / 47.053 | 30.880 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.584 / 14.442 | 4.559 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 34.197 / 34.183 | 2.728 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 32.646 / 33.691 | 0 / 9016 | 3.914 | -2.093 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.726 / 14.598 | 0 / 4508 | 0.394 | -0.961 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 33.414 / 33.418 | 0 / 4508 | 0.226 | -2.848 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.539 / 10.334 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 15.022 / 14.905 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 92.00 | 43.967 / 44.307 | 29.886 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_down | 92.00 | 21.325 / 21.385 | 12.656 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.726 / 14.598 | 4.285 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 33.414 / 33.418 | 2.453 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 32.671 / 31.715 | 0 / 8648 | 3.914 | -2.098 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.691 / 14.569 | 0 / 4324 | 0.394 | -0.957 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 33.413 / 33.421 | 0 / 4324 | 0.226 | -2.848 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.372 / 10.331 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 15.117 / 14.941 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 21.305 / 21.374 | 12.656 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 44.038 / 44.390 | 29.886 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.691 / 14.569 | 4.285 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 33.413 / 33.421 | 2.453 | `6ddf7aa8516c` | conditional_reference |

## qwen35-35b-a5-tp4-c64-graph:q4_b64_m256

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / DequantSwigluQuant | 40.00 | 54.031 / 54.304 | 0 / 0 | — | — | measured_cost_unavailable |
| C / GroupedMatmul | 80.00 | 51.347 / 53.046 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeCombineV3 | 40.00 | 27.371 / 28.149 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV3 | 40.00 | 28.796 / 29.044 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 40.00 | 24.071 / 23.750 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_ | 80.00 | 36.153 / 32.931 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|

## a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 34.113 / 34.658 | 0 / 7544 | 4.045 | -2.232 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.615 / 14.506 | 0 / 3772 | 0.419 | -0.925 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 34.207 / 34.204 | 0 / 3772 | 0.251 | -2.896 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.902 / 10.755 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 16.529 / 15.966 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 22.006 / 22.107 | 13.086 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 46.220 / 47.020 | 30.880 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.615 / 14.506 | 4.559 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 34.207 / 34.204 | 2.728 | `6ddf7aa8516c` | conditional_reference |

## a5_glm53flash_tp8_c4_p8k:q4_b4_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 51.435 / 51.334 | 462 / 0 | 1.934 | -0.226 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 98.458 / 98.182 | 0 / 462 | 3.043 | -1.092 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 21.821 / 21.538 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 4.524 / 4.452 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 22.909 / 21.233 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 51.435 / 51.334 | 46.054 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 98.439 / 98.184 | 72.458 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 98.510 / 98.089 | 72.458 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 31.612 / 31.679 | 0 / 9568 | 3.848 | -1.968 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.508 / 14.450 | 0 / 4784 | 0.369 | -0.966 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 32.913 / 32.904 | 0 / 4784 | 0.213 | -2.815 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.333 / 10.130 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 14.376 / 14.297 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 92.00 | 42.630 / 42.813 | 29.389 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_down | 92.00 | 20.594 / 20.584 | 12.441 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.508 / 14.450 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 32.913 / 32.904 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 31.626 / 32.952 | 0 / 9384 | 3.848 | -1.971 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.491 / 14.450 | 0 / 4692 | 0.369 | -0.964 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 32.982 / 32.979 | 0 / 4692 | 0.213 | -2.821 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 10.136 / 10.070 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 14.355 / 14.248 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 20.570 / 20.564 | 12.441 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 42.682 / 42.857 | 29.389 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.491 / 14.450 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 32.982 / 32.979 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 30.652 / 32.068 | 0 / 9752 | 3.848 | -1.792 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.448 / 14.367 | 0 / 4876 | 0.369 | -0.961 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.842 / 31.813 | 0 / 4876 | 0.213 | -2.716 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.848 / 9.768 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 13.885 / 13.800 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 20.066 / 20.058 | 12.441 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 41.239 / 41.265 | 29.389 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.448 / 14.367 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.842 / 31.813 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 30.784 / 32.222 | 0 / 9568 | 3.848 | -1.816 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.338 / 14.266 | 0 / 4784 | 0.369 | -0.950 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.864 / 31.860 | 0 / 4784 | 0.213 | -2.718 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.838 / 9.738 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 13.960 / 13.854 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 20.097 / 20.084 | 12.441 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 41.471 / 41.486 | 29.389 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.338 / 14.266 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.864 / 31.860 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 19.278 / 19.192 | 0 / 9936 | 3.848 | 0.301 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 34.585 / 34.645 | 0 / 4968 | 0.369 | -2.813 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.565 / 31.543 | 0 / 4968 | 0.213 | -2.691 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.890 / 9.805 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 14.024 / 14.025 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 92.00 | 22.335 / 22.320 | 29.389 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_down | 92.00 | 16.222 / 16.216 | 12.441 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 34.585 / 34.645 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.565 / 31.543 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 19.324 / 20.971 | 0 / 10120 | 3.848 | 0.293 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 34.497 / 34.534 | 0 / 5060 | 0.369 | -2.805 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.532 / 31.513 | 0 / 5060 | 0.213 | -2.688 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.985 / 9.815 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 13.954 / 13.974 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 92.00 | 22.426 / 22.406 | 29.389 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_down | 92.00 | 16.222 / 16.211 | 12.441 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 34.497 / 34.534 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.532 / 31.513 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## qwen36-a5-tp2-c96:q4_b96_m384

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| D / hcom_allReduce_ | 128.00 | 129.800 / 127.204 | 0 / 3072 | 10.200 | -6.414 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 127.813 / 127.705 | 79.691 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 126.719 / 126.499 | 79.691 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 127.942 / 127.499 | 79.691 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 127.926 / 127.689 | 79.691 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 429.909 / 126.384 | 79.691 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 127.572 / 127.300 | 79.691 | `d5345a2d23c0` | conditional_reference |

## glm53flash-a5-tp8-c3:q4_b4_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 51.524 / 51.382 | 2226 / 0 | 1.934 | -0.230 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 98.728 / 98.517 | 0 / 2226 | 3.043 | -1.103 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 20.738 / 20.654 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 4.259 / 4.257 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 24.738 / 21.280 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 51.524 / 51.382 | 46.054 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 98.926 / 98.791 | 72.458 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 98.658 / 98.458 | 72.458 | `6ddf7aa8516c` | conditional_reference |

## glm53flash-a5-tp8-c1:q4_b1_m4

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 42.00 | 22.482 / 22.473 | 2730 / 0 | 0.484 | -0.460 | complete_cost_coverage |
| C / GroupedMatmulSwigluQuantV2 | 42.00 | 33.520 / 33.429 | 0 / 2730 | 0.763 | -0.645 | complete_cost_coverage |
| B / MoeInitRoutingV3 | 42.00 | 20.796 / 20.692 | 0 / 0 | — | — | measured_cost_unavailable |
| B / _copy_conv_state_kernel | 68.00 | 3.684 / 3.564 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_AicpuKernel | 90.00 | 21.928 / 18.015 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 42.00 | 22.482 / 22.473 | 11.527 | `e78bca41dba4` | strict_cohort |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.00 | 33.521 / 33.389 | 18.156 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.00 | 33.520 / 33.438 | 18.156 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 186.707 / 189.835 | 0 / 5840 | 12.961 | -1.976 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 15.402 / 15.216 | 0 / 2920 | 0.278 | -0.338 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 21.045 / 19.659 | 0 / 2920 | 0.184 | -0.658 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 123.273 / 122.228 | 107.421 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 250.141 / 248.818 | 216.600 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 15.402 / 15.216 | 6.949 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 21.045 / 19.659 | 4.592 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 181.227 / 185.000 | 0 / 6000 | 12.925 | -1.573 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 19.057 / 18.962 | 0 / 3000 | 0.221 | -0.541 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 19.944 / 18.578 | 0 / 3000 | 0.128 | -0.670 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 119.854 / 118.821 | 107.298 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 242.599 / 241.331 | 215.839 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 19.057 / 18.962 | 5.526 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 19.944 / 18.578 | 3.196 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 19.004 / 20.487 | 0 / 10856 | 3.848 | 0.352 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.550 / 14.394 | 0 / 5428 | 0.369 | -0.970 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.319 / 31.314 | 0 / 5428 | 0.213 | -2.668 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.035 / 8.391 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 13.567 / 12.664 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 92.00 | 16.052 / 16.026 | 12.441 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_up | 92.00 | 21.957 / 21.948 | 29.389 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.550 / 14.394 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.319 / 31.314 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 184.00 | 18.982 / 19.038 | 0 / 10856 | 3.848 | 0.356 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 92.00 | 14.544 / 14.416 | 0 / 5428 | 0.369 | -0.969 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 92.00 | 31.335 / 31.323 | 0 / 5428 | 0.213 | -2.670 | complete_cost_coverage |
| D / hcom_allGather_ | 187.00 | 9.110 / 8.344 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 186.00 | 13.590 / 12.643 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 92.00 | 21.918 / 21.895 | 29.389 | `e78bca41dba4` | conditional_reference |
| GroupedMatmul / expert_down | 92.00 | 16.045 / 16.026 | 12.441 | `e78bca41dba4` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 92.00 | 14.544 / 14.416 | 4.007 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 92.00 | 31.335 / 31.323 | 2.315 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 96.322 / 98.585 | 0 / 8400 | 6.463 | -1.243 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 12.381 / 12.229 | 0 / 4200 | 0.197 | -0.298 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 18.548 / 17.867 | 0 / 4200 | 0.115 | -0.627 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 65.238 / 64.668 | 53.651 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 127.406 / 126.789 | 107.922 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 12.381 / 12.229 | 4.923 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 18.548 / 17.867 | 2.865 | `6ddf7aa8516c` | conditional_reference |

## qwen35-35b-a5-tp4-c4-graph:q4_b4_m16

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / DequantSwigluQuant | 40.00 | 7.299 / 7.286 | 0 / 0 | — | — | measured_cost_unavailable |
| C / GroupedMatmul | 80.00 | 27.975 / 26.755 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeCombineV3 | 40.00 | 11.678 / 11.374 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV3 | 40.00 | 17.246 / 16.954 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 40.00 | 10.573 / 10.290 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_ | 80.00 | 26.415 / 25.215 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|

## a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 31.099 / 33.455 | 0 / 11600 | 1.616 | -0.872 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 11.209 / 11.140 | 0 / 5800 | 0.172 | -0.276 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 29.449 / 16.841 | 0 / 5800 | 0.105 | -1.073 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 23.656 / 23.572 | 13.416 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 38.541 / 38.378 | 26.983 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 11.209 / 11.140 | 4.297 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 29.449 / 16.841 | 2.617 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 52.757 / 53.674 | 0 / 10320 | 3.232 | -0.989 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 11.810 / 11.729 | 0 / 5160 | 0.185 | -0.288 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 17.898 / 17.041 | 0 / 5160 | 0.108 | -0.608 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_up | 40.00 | 68.076 / 67.778 | 53.963 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_down | 40.00 | 37.439 / 37.167 | 26.828 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 11.810 / 11.729 | 4.621 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 17.898 / 17.041 | 2.700 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 31.206 / 31.887 | 0 / 12080 | 1.616 | -0.881 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 11.254 / 11.175 | 0 / 6040 | 0.172 | -0.278 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 47.766 / 35.270 | 0 / 6040 | 0.105 | -1.806 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 23.604 / 23.476 | 13.416 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 38.809 / 38.660 | 26.983 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 11.254 / 11.175 | 4.297 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 47.766 / 35.270 | 2.617 | `6ddf7aa8516c` | conditional_reference |

## a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 80.00 | 31.115 / 33.644 | 0 / 12160 | 1.616 | -0.873 | complete_cost_coverage |
| A / MoeDistributeCombineV3 | 40.00 | 11.198 / 11.141 | 0 / 6080 | 0.172 | -0.276 | complete_cost_coverage |
| A / MoeDistributeDispatchV3 | 40.00 | 45.332 / 33.641 | 0 / 6080 | 0.105 | -1.709 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 40.00 | 23.639 / 23.543 | 13.416 | `6ddf7aa8516c` | conditional_reference |
| GroupedMatmul / expert_up | 40.00 | 38.592 / 38.458 | 26.983 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeCombineV3 / expert_combine_native | 40.00 | 11.198 / 11.141 | 4.297 | `6ddf7aa8516c` | conditional_reference |
| MoeDistributeDispatchV3 / expert_dispatch_native | 40.00 | 45.332 / 33.641 | 2.617 | `6ddf7aa8516c` | conditional_reference |

## qwen36-a5-tp2-c12:q4_b12_m48

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| D / hcom_allReduce_ | 128.00 | 43.805 / 39.726 | 0 / 7040 | 5.430 | -0.177 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 46.438 / 45.606 | 42.420 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 39.694 / 39.648 | 42.420 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 39.279 / 39.225 | 42.420 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 39.208 / 39.168 | 42.420 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 263.503 / 38.802 | 42.420 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 39.537 / 39.662 | 42.420 | `d5345a2d23c0` | conditional_reference |

## qwen36-a5-tp2-c1:q4_b1_m4

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| D / hcom_allReduce_ | 128.00 | 10.833 / 9.960 | 0 / 10880 | 0.528 | -0.858 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 10.946 / 10.573 | 4.129 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 47.00 | 10.176 / 9.834 | 4.129 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 10.640 / 9.762 | 4.129 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 16.00 | 10.084 / 9.691 | 4.129 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 50.935 / 9.400 | 4.129 | `d5345a2d23c0` | conditional_reference |
| hcom_allReduce_ / allreduce_explicit_source_collective | 1.00 | 11.330 / 11.523 | 4.129 | `d5345a2d23c0` | conditional_reference |

## v4flash-a3-tp8-c4:q2_b4_m8

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| A / MoeDistributeCombineV2 | 43.00 | 20.941 / 19.439 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV2 | 43.00 | 40.954 / 40.870 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 43.00 | 29.415 / 28.459 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_ | 86.00 | 21.779 / 18.159 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|

## a3_kimi4_tp8_w4a8_c32:q1_b32_m32

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 6.00 | 467.534 / 455.321 | 0 / 1320 | 3.102 | 0.296 | complete_cost_coverage |
| A / MoeDistributeCombineV2 | 3.00 | 42.028 / 39.630 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV2 | 3.00 | 58.279 / 58.639 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 9.00 | 60.319 / 28.699 | 0 / 1540 | 0.031 | -0.455 | partial_cost_coverage |
| D / hcom_reduceScatter_ | 8.00 | 25.915 / 21.820 | 0 / 1760 | 0.043 | -0.164 | complete_cost_coverage |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 3.00 | 303.243 / 302.704 | 345.826 | `fd8238dbb993` | conditional_reference |
| GroupedMatmul / expert_up | 3.00 | 631.825 / 633.147 | 688.064 | `fd8238dbb993` | conditional_reference |
| hcom_allGather_ / allgather_explicit_source_collective | 2.00 | 26.834 / 26.549 | 4.447 | `d5345a2d23c0` | conditional_reference |
| hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 48.289 / 21.860 | 4.447 | `d5345a2d23c0` | conditional_reference |
| hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 28.996 / 28.939 | 4.447 | `d5345a2d23c0` | conditional_reference |
| hcom_allGather_ / allgather_explicit_source_collective | 1.00 | 221.270 / 202.216 | 4.447 | `d5345a2d23c0` | conditional_reference |
| hcom_allGather_ / allgather_explicit_source_collective | 2.00 | 66.885 / 31.939 | 4.447 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 2.00 | 23.497 / 23.719 | 5.355 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 2.00 | 20.911 / 18.380 | 5.355 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 41.500 / 29.329 | 5.355 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 29.563 / 29.349 | 5.355 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 25.296 / 18.410 | 5.355 | `d5345a2d23c0` | conditional_reference |
| hcom_reduceScatter_ / reduce_scatter_explicit_source_collective | 1.00 | 22.145 / 22.200 | 5.355 | `d5345a2d23c0` | conditional_reference |

## a3_glm53_w4a8_tp16_tpot88_c8:q6_b8_m48

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| A / MoeDistributeCombineV2 | 75.00 | 40.227 / 40.341 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV2 | 75.00 | 31.623 / 31.420 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 75.00 | 40.732 / 40.421 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allReduce_ | 156.00 | 41.294 / 39.981 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|

## a3_kimi4_tp8_w4a8_c1:q1_b1_m1

| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |
|---|---:|---:|---:|---:|---:|---|
| C / GroupedMatmul | 6.00 | 47.226 / 48.369 | 0 / 1524 | 0.794 | 0.511 | complete_cost_coverage |
| A / MoeDistributeCombineV2 | 3.00 | 20.267 / 18.600 | 0 / 0 | — | — | measured_cost_unavailable |
| A / MoeDistributeDispatchV2 | 3.00 | 54.373 / 54.379 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_allGather_ | 9.00 | 80.921 / 26.130 | 0 / 0 | — | — | measured_cost_unavailable |
| D / hcom_reduceScatter_ | 8.00 | 27.729 / 18.960 | 0 / 0 | — | — | measured_cost_unavailable |

Component costs (each retains its own measured population and runtime):

| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |
|---|---:|---:|---:|---|---|
| GroupedMatmul / expert_down | 3.00 | 38.730 / 39.539 | 89.061 | `fd8238dbb993` | conditional_reference |
| GroupedMatmul / expert_up | 3.00 | 55.722 / 55.499 | 175.598 | `fd8238dbb993` | conditional_reference |

Full integer duration histograms, excluded overlapping alternatives, source/case/receipt hashes, physical program references and conditions remain in JSON. Current Body and operator families may originate from different runtime generations; the ledger does not relabel them.
