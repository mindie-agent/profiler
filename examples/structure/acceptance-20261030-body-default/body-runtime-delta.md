# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.9568 | 10.2228 | 10.1755 | -0.0473 | -53.4414% | -53.6568% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.5848 | 14.6508 | 14.6499 | -0.0009 | -48.7461% | -48.7491% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.5514 | 5.0519 | 5.0658 | 0.0139 | -56.2655% | -56.1455% |
| qwen36-a5-tp2-c12:q4_b12_m48 | 24.2258 | 10.9985 | 10.6426 | -0.3559 | -54.6000% | -56.0692% |
| qwen36-a5-tp2-c96:q4_b96_m384 | 63.8534 | unavailable | 40.9721 | unavailable | unavailable | -35.8341% |
| qwen36-a5-tp2-c1:q4_b1_m4 | 12.3183 | 7.4129 | 7.3822 | -0.0307 | -39.8221% | -40.0711% |
| qwen35-397b-a3-tp16-c48:q4_b64_m256 | 76.0890 | 68.0980 | 67.8843 | -0.2137 | -10.5021% | -10.7830% |
| qwen35-397b-a3-tp16-c136:q4_b160_m640 | 119.0543 | 102.2110 | 101.3711 | -0.8400 | -14.1476% | -14.8531% |
| a3_glm53_dc4k_b2:q1_b2_m2 | 40.9699 | 35.4171 | 31.5613 | -3.8558 | -13.5533% | -22.9647% |
| a3_glm53_dc4k_b4:q1_b4_m4 | 43.4377 | 38.5624 | 34.7067 | -3.8557 | -11.2237% | -20.1001% |
| a3_glm53_dc16k_b1:q1_b1_m1 | 39.1121 | 33.5730 | 29.7171 | -3.8559 | -14.1621% | -24.0207% |
| a3_glm53_dc4k_b1:q1_b1_m1 | 38.9548 | 33.5730 | 29.7171 | -3.8559 | -13.8156% | -23.7139% |
| a3_glm53_dc4k_b8:q1_b8_m8 | 47.1133 | 44.0502 | 40.1948 | -3.8554 | -6.5015% | -14.6848% |
| glm53flash-a3-tp16-c16-livepre:q6_b16_m96 | 41.0691 | 59.1761 | 47.5496 | -11.6265 | 44.0892% | 15.7796% |
| glm53flash-a5-tp8-c1:q4_b1_m4 | 15.6833 | 9.5014 | 8.5942 | -0.9073 | -39.4171% | -45.2020% |
| glm53flash-a5-tp8-c3:q4_b4_m16 | 21.0675 | 14.0282 | 13.1313 | -0.8968 | -33.4134% | -37.6704% |
| glm53flash-a3-tp16-c4-livepre:q6_b4_m24 | 29.7616 | 34.9335 | 31.6870 | -3.2465 | 17.3779% | 6.4695% |
| glm53flash-a3-tp16-c2:q6_b2_m12 | 34.1185 | 28.5665 | 26.2332 | -2.3333 | -16.2726% | -23.1114% |
| glm53flash-a3-tp16-c4:q6_b4_m24 | 39.8413 | 34.9335 | 31.6870 | -3.2465 | -12.3184% | -20.4671% |
| glm53flash-a5-tp8-c96:q4_b96_m384 | 57.5897 | unavailable | 40.5286 | unavailable | unavailable | -29.6253% |
| v4flash-a3-tp8-c4:q2_b4_m8 | 32.4860 | 26.4453 | 24.1503 | -2.2951 | -18.5945% | -25.6594% |
| v4flash-a3-tp8-c8:q2_b8_m16 | 37.7631 | 33.4637 | 31.1603 | -2.3034 | -11.3854% | -17.4849% |

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
