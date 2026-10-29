# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c16_p4k:q1_b16_m16 | 36.9853 | 25.9897 | 25.9445 | -0.0453 | -29.7295% | -29.8519% |
| a5_kimi_tp8_e16_bf16_c1_p4k:q1_b1_m1 | 30.6369 | 23.0206 | 22.9741 | -0.0465 | -24.8598% | -25.0114% |
| a5_kimi_tp8_e16_bf16_c2_p4k:q1_b2_m2 | 33.5476 | 23.1674 | 23.1209 | -0.0465 | -30.9419% | -31.0804% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.0187 | 29.9263 | 29.8834 | -0.0429 | -25.2193% | -25.3264% |
| a5_kimi_tp8_e16_bf16_c4_p4k:q1_b4_m4 | 34.1937 | 23.4609 | 23.4144 | -0.0465 | -31.3883% | -31.5242% |
| a5_kimi_tp8_e16_bf16_c8_p4k:q1_b8_m8 | 34.8192 | 24.0466 | 24.0001 | -0.0465 | -30.9388% | -31.0722% |
| a5_kimi_tp8_e16_bf16_c16_p16k:q1_b16_m16 | 39.2474 | 27.2001 | 27.1548 | -0.0453 | -30.6958% | -30.8112% |
| a5_kimi_tp8_e16_bf16_c1_p16k:q1_b1_m1 | 30.8234 | 23.0963 | 23.0498 | -0.0465 | -25.0692% | -25.2199% |
| a5_kimi_tp8_e16_bf16_c2_p16k:q1_b2_m2 | 33.8758 | 23.3187 | 23.2722 | -0.0465 | -31.1642% | -31.3013% |
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.6662 | 32.3469 | 32.3041 | -0.0429 | -27.5807% | -27.6767% |
| a5_kimi_tp8_e16_bf16_c4_p16k:q1_b4_m4 | 34.8165 | 23.7635 | 23.7170 | -0.0465 | -31.7466% | -31.8800% |
| a5_kimi_tp8_e16_bf16_c8_p16k:q1_b8_m8 | 35.9644 | 24.6517 | 24.6053 | -0.0465 | -31.4552% | -31.5844% |

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
