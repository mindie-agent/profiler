# V4.1 source-body conditions against seven retained captures

Seven captures / 830 measured complete forwards; fourteen explicit peer-load conditions. This is an additional conditional comparison, not a replacement for the 66-case baseline. Neither condition is selected by smaller error.

| Capture | Execution B | Forwards | Real mean / P50 / P90 ms | Single rank0-active ms | Difference vs mean | Symmetric [B]×8 ms | Difference vs mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| c4_p2k | 1 | 151 | 13.239 / 13.209 / 13.227 | 6.984 | -47.2% | 9.722 | -26.6% |
| tpot10ms_c8 | 1 | 145 | 13.292 / 12.803 / 12.817 | 6.984 | -47.5% | 9.722 | -26.9% |
| tpot5ms_c1 | 1 | 152 | 13.135 / 13.129 / 13.145 | 6.984 | -46.8% | 9.722 | -26.0% |
| c16_p2k | 2 | 129 | 14.929 / 14.914 / 14.929 | 7.553 | -49.4% | 13.030 | -12.7% |
| c32_p2k | 4 | 105 | 18.625 / 18.616 / 18.640 | 8.145 | -56.3% | 19.644 | +5.5% |
| tpot30ms_c64 | 8 | 75 | 26.328 / 26.306 / 26.336 | 9.888 | -62.4% | 32.886 | +24.9% |
| c128_p2k | 16 | 73 | 27.286 / 27.266 / 27.290 | 13.409 | -50.9% | 33.237 | +21.8% |

All predictions execute the full declared 40-layer body. The original ledger has 11 successes and three 60-second timeouts; the three explicit c226 retries complete with exactly the same input SHA and geometry under the same 60-second budget. Both attempts remain in the JSON. Each package_start equals package_end; every worker stays below 512 MiB.

Real values are the retained rank0 device-event envelopes. Sim duration is completion of the declared cohort from input readiness; endpoint and peer-load equivalence are not observed. Shape-derived B is execution geometry, not proof of valid active requests on every DP rank. Source programs, route-mask/group-list values and per-forward active KV length remain conditional.

Family activity is retained only as a nonadditive diagnostic across all declared participants; it includes contention and is not a decomposition of rank0 wall time.

Validation: 544 checks, zero raw reads and zero new predictions. Unique observed population is counted once; no 14-capture or combined-accuracy claim.
