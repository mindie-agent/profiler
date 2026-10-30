# A3 GLM78 complete SFA pipeline observations

The three populations reuse retained Body windows and full native ABI/timing histograms. No new device run or prediction was executed.

| Case | Forwards | Calls | Mean / P50 us | AIC sum−elapsed / max−elapsed us | AIV sum−elapsed / max−elapsed us |
|---|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2 | 44 | 3432 | 95.769 / 95.082 | -17.826 / -75.273 | 18.654 / -50.552 |
| a3_glm53_w4a8_tp16_tpot50_c2 | 44 | 3432 | 95.759 / 95.082 | -17.838 / -75.260 | 18.643 / -50.570 |
| a3_glm53_w4a8_tp16_tpot88_c8 | 49 | 3822 | 209.252 / 209.144 | 91.039 / -125.752 | 154.053 / -72.081 |

All sums and maxima are paired per call before aggregation. Pipeline times overlap; neither sum nor maximum is automatically a wall-time model. Raw numeric/missing/zero denominators and full histograms are retained in JSON.

The three pipeline columns use 3,432 / 3,430 / 3,809 complete PMU pairs respectively; 0 / 2 / 13 calls have missing PMU values. The elapsed Mean/P50 column retains all 3,432 / 3,432 / 3,822 calls. Missing values are not zeros. All calls have Block Num 20 and Mix Block Num 40.

For c8 the valid-PMU means are AIC 164.826 us and AIV 165.408 us; AIV scalar is 137.168 us, vector 120.922 us, MTE2 77.227 us, MTE3 27.985 us, while AIC Fixpipe is 83.497 us. These constrain concurrent source pipelines; they do not establish mutually exclusive stage durations. The full-population native elapsed mean is 209.252 us.

These CSV headers export instruction-cache miss rates and MTE time, but no HBM/DDR byte counts, tensor-data L2 byte counts, or data-L2 hit rate. Consequently these observations do not identify a scratch-cache hit rate or validate moving the declared off-chip scratch traffic into L2.
