# Decode Body runtime comparison

Identical retained source populations; no raw capture reads or new prediction in this join.

| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |
|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c64-graph:q4_b64_m256 | 21.9568 | 10.9417 | 11.7235 | 0.7818 | -50.1674% | -46.6066% |
| qwen35-35b-a5-tp4-c128-graph:q4_b128_m512 | 28.5848 | 14.8448 | 16.6217 | 1.7769 | -48.0673% | -41.8512% |
| qwen35-35b-a5-tp4-c4-graph:q4_b4_m16 | 11.5514 | 5.3677 | 4.7058 | -0.6618 | -53.5320% | -59.2616% |

Prior/current failures before geometry extraction retained separately: 0/0.

A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.
Body wall time is distinct from accumulated operator activity or isolated service time.
