# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1:q1_b1_m1 | 13.1346 | 8.1629 | 7.4302 | -0.7327 | -37.8520% | -43.4302% |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k:q1_b2_m2 | 14.9293 | 9.8057 | 9.0784 | -0.7273 | -34.3192% | -39.1910% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.2860 | 19.9894 | 19.2448 | -0.7446 | -26.7412% | -29.4701% |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8:q1_b1_m1 | 13.2916 | 8.1629 | 7.4302 | -0.7327 | -38.5859% | -44.0982% |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k:q1_b4_m4 | 18.6246 | 13.0913 | 12.3608 | -0.7305 | -29.7093% | -33.6315% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.3282 | 19.6753 | 18.9325 | -0.7427 | -25.2694% | -28.0904% |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k:q1_b1_m1 | 13.2388 | 8.1629 | 7.4302 | -0.7327 | -38.3412% | -43.8754% |
| a5_kimi_k3_p32768_c1:q1_b1_m1 | 32.5555 | unavailable | 28.5606 | unavailable | unavailable | -12.2711% |

Prior/current failures before geometry extraction retained separately: 0/0.

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
