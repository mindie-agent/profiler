# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.0675 | 13.0576 | 11.8026 | -1.2550 | -38.0203% | -43.9774% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.5897 | 65.1450 | 59.3680 | -5.7770 | 13.1192% | 3.0879% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.6833 | 7.9372 | 6.8297 | -1.1076 | -49.3907% | -56.4526% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.0309 | 21.9794 | 20.1346 | -1.8448 | -33.4581% | -39.0433% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.6161 | 22.1668 | 20.3220 | -1.8448 | -34.0589% | -39.5468% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.6690 | 27.7425 | 25.1113 | -2.6313 | -26.3517% | -33.3370% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.7132 | 28.1218 | 25.4905 | -2.6313 | -27.3587% | -34.1555% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.4182 | 11.9359 | 10.6809 | -1.2550 | -44.2723% | -50.1318% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.5282 | 38.7232 | 34.5190 | -4.2041 | -16.7749% | -25.8106% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.8333 | 18.0709 | 16.6193 | -1.4516 | -37.3264% | -42.3609% |

Prior/current failures before geometry extraction retained separately: 0/0.

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
