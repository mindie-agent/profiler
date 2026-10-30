# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c32_p16k:q1_b32_m32 | 44.6662 | 33.7305 | 33.7306 | 0.0001 | -24.4831% | -24.4828% |
| a5_kimi_tp8_e16_bf16_c32_p4k:q1_b32_m32 | 40.0187 | 28.5438 | 28.5439 | 0.0001 | -28.6740% | -28.6737% |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64:q1_b8_m8 | 26.3282 | 18.9325 | 18.9326 | 0.0001 | -28.0904% | -28.0901% |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k:q1_b16_m16 | 27.2860 | 19.2448 | 19.2450 | 0.0002 | -29.4701% | -29.4692% |

Prior/current failures before geometry extraction retained separately: 0/0.

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
