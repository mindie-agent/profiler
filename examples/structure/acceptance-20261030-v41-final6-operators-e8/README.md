# V4.1 final six: source-bound body operator comparisons

This batch processes five A3 TP4/DP4/EP16 W8A8 DSpark7 captures and A5 TP1/DP8/EP8 FP8/FP4 c128. The model inputs are commit `d08be4d4` and the physical runtime is its `e8` generation. Runtime costs use the existing detached checkout; the full source SHA map is retained in each report. Resolved quantization was checked before execution.

The six complete source extractions contain **457 body forwards**. This operator pass deliberately chooses each source's largest measured geometry, totaling **225 body forwards**: A3 c4/c8/c16/c32/c64 use q8 and execution B2/B4/B5/B9/B17; A5 c128 uses q1/B16. Client concurrency is separate from this padding/execution geometry. Representative contexts are A3 4096 and A5 2048, not observed active KV lengths. Every source was streamed once for this batch; source extraction totals 106.072 seconds and stays below 475 MiB.

The strict result is **60/63 passing cohorts, all in the <=50 us / absolute 15 us tier**. The three failures are the A3 `compress_gates|compress_values` MatMulV2 family at c4/c32/c64. **Fourteen conditional source-program groups** remain outside strict pass/fail counts. The independent review passes 3,266 identity, histogram, tolerance and population checks, including exact 39-layer steady histograms.

## Atomic routed FFN boundary

The real A3 `DispatchFFNCombine` eight-input/two-output ABI now maps to a conditional routed-only program set: packing, dispatch, activation quantization, expert gate/up, SwiGLU, output quantization, expert down, combine and unpack. Router/top-k, shared experts, join, norms and hyper-connections remain external. Source buffer capacity, active-mask values and valid routed rows are explicitly different quantities. The reference executes the complete declared DP cohort once; it does not add all replica costs as single-card latency.

| A3 client concurrency | Measured mean/P50 us | Declared reference us | Measured activity ms/forward | Declared service ms/forward | Conditional residual ms/forward |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 | 712.08/695.77 | 915.82 | 28.483 | 36.633 | +8.150 |
| 8 | 694.02/691.05 | 921.87 | 27.761 | 36.875 | +9.114 |
| 16 | 698.50/695.16 | 924.93 | 27.940 | 36.997 | +9.057 |
| 32 | 718.05/712.57 | 940.67 | 28.722 | 37.627 | +8.905 |
| 64 | 718.43/712.58 | 972.70 | 28.737 | 38.908 | +10.171 |

The +8.15 to +10.17 ms/forward residual is a conditional existing-program comparison, not an additive causal body budget. The reference has separate launches and generic transport; the captured atomic MC2 fusion and scheduling are not established by it. No extra work may be added for these already-declared programs.

## Control-wrapper evidence

`reduce_scatterAicpuKernel` is retained in this generation as an unresolved control-wait candidate, around 5.5 ms/forward in the A3 primary populations. It must not be counted as additional device service or used to fit bandwidth. A bounded historical two-body probe finds 86 typed AI_CPU events, but HCOM task/stream identities are absent, so same-task association is unproven. An in-process alias trial leaves those two body spans unchanged while changing activity/gap and two layer statistics. Production parsing was not changed; `reduce-scatter-wrapper-alias-evidence.json` retains exact row/time evidence for the next generation.

Artifacts: `body-operator-family-scoreboard.json`, `.md`, `body-operator-family-independent-review.json`, and `steady-layer-pooled.json`.
