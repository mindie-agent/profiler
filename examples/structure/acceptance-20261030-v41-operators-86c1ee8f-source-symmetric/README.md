# V4.1 A5 source-symmetric conditional operator arm

This arm uses the seven explicit `v41-source-conditional/*-source.json` inputs at Sim `86c1ee8f18b9b997eacb315476e2461b99b59fb1`. Each retained `sequences=B` declaration expands to the symmetric DP condition `[B]*8`; it is not an observation that every DP replica has B valid active requests. No `single_active_rank0` operator arm is inferred here.

The source cases select MXA8W4 NZ grouped matrices, mixed-packed MQSMLA, and explicit HC source traffic recipes. Complete retained native GroupedMatmul ABI partitions can be revalidated against the fresh physical programs. Unknown route-mask/group-list values and valid routed rows remain unknown. Source binary identity is not established. Reference errors therefore remain conditional and are never strict accuracy passes.

Each per-case directory contains a fresh mapping, strict physical-program predictions, source references, runtime and input fingerprints, and an independent arithmetic review. `queue-receipt.json` records the serial execution outcomes, including any failed process. The final `v41-seven-arm-comparison.json/.md` joins the two conditions only after verifying identical measured populations; it does not pool their strict denominators.

Reproduction is the baseline repricing command with an explicit `--case <fixed>/examples/cases/high-concurrency-20261030/v41-source-conditional/<capture>-source.json`, `--variant runtime86-source-symmetric`, and one output directory per case. Reuse the original actual/mapping metadata; do not replace measured input geometry or rewrite the original receipts.

`cache-builder-equivalence.json` independently compares the pre-cache `d1cd8436` builder and cached `86c1ee8f` builder on the same source-symmetric q1/B1 up/down programs. The public operator results and all 1,000 Engine task traces per operator are equal, including service and completion time. The audit reads the historical builder directly from Git into memory; it creates no checkout copy and reads no capture timing. Other physical model changes between older runtimes and 86c are outside that cache-only equivalence claim.
