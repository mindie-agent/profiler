# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.0675 | 13.0253 | 13.0576 | 0.0323 | -38.1739% | -38.0203% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.5897 | 64.3687 | 65.1450 | 0.7763 | 11.7712% | 13.1192% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.6833 | 7.9291 | 7.9372 | 0.0081 | -49.4422% | -49.3907% |
| a5_glm53flash_tp8_c16_p4k:q4_b16_m64 | 33.0309 | 21.8500 | 21.9794 | 0.1294 | -33.8499% | -33.4581% |
| a5_glm53flash_tp8_c16_p8k:q4_b16_m64 | 33.6161 | 22.0374 | 22.1668 | 0.1294 | -34.4438% | -34.0589% |
| a5_glm53flash_tp8_c32_p4k:q4_b32_m128 | 37.6690 | 27.4838 | 27.7425 | 0.2588 | -27.0387% | -26.3517% |
| a5_glm53flash_tp8_c32_p8k:q4_b32_m128 | 38.7132 | 27.8630 | 28.1218 | 0.2588 | -28.0271% | -27.3587% |
| a5_glm53flash_tp8_c4_p8k:q4_b4_m16 | 21.4182 | 11.9036 | 11.9359 | 0.0323 | -44.4233% | -44.2723% |
| a5_glm53flash_tp8_c64_p4k:q4_b64_m256 | 46.5282 | 38.2056 | 38.7232 | 0.5175 | -17.8872% | -16.7749% |
| a5_glm53flash_tp8_c8_p4k:q4_b8_m32 | 28.8333 | 18.0062 | 18.0709 | 0.0647 | -37.5507% | -37.3264% |

Prior/current failures before geometry extraction retained separately: 0/0.

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
