# Physical service observations

These tables support the shared profiler/Sim micro-instruction and network
modeling work. They reuse local A3/A5 captures and preserve measured populations,
units, native boundaries, source identities and explicit source conditions.
Observable small-payload and low-M responses are valid model parameters.
Their calibration provenance is independent of accuracy admission.

| Evidence | Measured population | Usable model boundary |
|---|---|---|
| [Scalar, DMA and routing](arch3510-physical-services/scalar-dma-physical-constraints.md) | Six A5 sources, 345 complete Body forwards, 69 ABI/Block partitions | Native-call service and directional source-program pipeline response |
| [Routing source inventory](arch3510-physical-services/scalar-dma-routing-source-join.md) | Three complete routing populations, 4,452 calls in 106 Forwards | Per-owner SIMT, scalar and sorting-macro counts; thirteen coordinates span three measured design dimensions |
| [MC2 PMU](arch3510-physical-services/mc2-observable-pmu-baseline.md) | 46 A3/A5 sources, 710 native groups, 327,288 calls | Separate V2/V3 dispatch/combine and fused dispatch/FFN/combine envelopes |
| [MC2 source counts](arch3510-physical-services/mc2-source-count-constraints.md) | Four A5 domains, 16 populations, 37,480 calls in 332 Forwards | Per-owner source work joined to complete native PMU populations; Layer 0 and steady service remain separate |
| [A3 grouped matrix](arch22-physical-services/grouped-source-constraints.md) | Three GLM78 sources, 137 Forwards, 20,550 calls, six ABI/Block partitions | Complete native-call responses plus conditional source tile counts and original PMU denominators |
| [A5 grouped matrix](arch3510-physical-services/grouped-source-constraints.md) | Three Qwen3.5 sources, 239 Forwards, 19,120 calls, twelve partitions | Separate INT32 gate-up and BF16 down programs, retaining GDN/GQA layer populations |
| [Conditional HCCL services](arch3510-physical-services/network-observable-service-baseline.md) | Seven sources, 56 complete groups, 52,972 calls | Engine/template/rank/payload-conditioned collective elapsed service |
| [A3 network observations](arch22-physical-services/network/README.md) | Four microbench runs, 96 rank-specific points, 42 trace envelopes; 25 model sources | Observed SIO/HCCS_SW paths for two/four ranks, separate TP8/TP16 whole-call services |

The datasets overlap. Their source, call and Forward counts must not be summed
into new captures or additional model accuracy samples. Each JSON retains the
original pins and exact histogram/partition locators.

## Wave 1: parameter granularity

| Requested primitive | Current evidence and parameter scope |
|---|---|
| Scalar GetValue/ALU | Complete scalar busy populations and source counts. Copy-program slopes are 181.161 ns for gather and 136.334 ns for scatter; each includes the stated source schedule. Independent GetValue and ALU prices are not isolated. |
| MTE2/MTE3 descriptors | Gather/scatter MTE2 slopes are 298.518/133.207 ns per source program; MTE3 slopes are 139.955/134.413 ns. These are usable composite responses. Program count, metadata loads and bytes are collinear in this sample. |
| SIMT atomic RMW | Routing ABI, BlockNum and pipeline observations are available. Transaction collisions and atomic instruction elapsed are not separately measured by these captures. |
| VBitSort32/VMrgSort4V2 | Routing source work can be joined to measured vector service. A native routing envelope does not independently identify each sort opcode's cycles. |
| Flags and barriers | Signed pipeline diagnostics and task wait are retained. `elapsed - sum(pipes)` may be negative because pipes overlap; `elapsed - max(pipes)` does not identify SyncAll by itself. |

Source-program responses can be consumed immediately in their observed domain.
Splitting a joint response into new primitives needs independently varying
instruction counts or a direct counter; it does not require reconstructing a
driver. Inclusive native responses and their internal pipeline prices must not
be charged twice.

The MC2 join demonstrates why owner scope matters: Kimi Combine's all-owner
UB call count grows 7.23 times from c1 to c32 while its maximum per-owner count
stays fixed and scalar busy decreases. Each within-domain design has only two
points for eight candidate columns. These observations constrain a joint service
model; a pooled cross-model full-rank matrix would not identify independent
instruction prices. V4.1 Layer 0 also has the same declared source program as
steady layers but a different measured response.

Grouped PMU fields with missing samples retain their own numeric denominator.
For example, A3 c8 has 3,661 numeric PMU records among 3,675 complete native
calls per grouped boundary. A5 c128 down has identical allocated geometry and
BlockNum across GDN/GQA, yet means differ (45.415/37.262 us), so the domains
remain separate. Neither allocated capacity nor BlockNum establishes actual
routed rows or a compiled DMA descriptor count.

## Wave 2: parameter granularity

The A3 observations include captured physical-path labels and ordered SDMA,
notify, event and write-value tasks. A5 groups retain observed execution engines
and source-declared templates/payloads. Effective fixed-plus-bandwidth services
can be fitted within those domains. Reported payload is distinct from wire
traffic and from adjacent tensor-size candidates.

Exact 4 KiB payloads, a measured UB_CLOS path, per-phase routes for the TP8/TP16
model captures, and isolated receiver-incast timing are not present in this
first export. A collective's fixed component includes controller issue,
protocol, peer readiness and possible switch service; it is not a uniquely
measured switch-hop RTT. Sim's Tx/Rx contention and hop resources can consume
this evidence with those distinctions preserved.

## Integration

Wave 0 numerical results are maintained in the
[ordered three-level scoreboard](../../../examples/structure/acceptance-20261030-priority/priority-three-level-scoreboard.md).
Each replacement follows source/case identity and declared input order, including
regressions. Source and runtime hashes remain in the replay receipts. Body,
layer and operator tolerances remain separate, and a new Body result does not
silently recost old operator receipts.

One actual graph gap found during this export is GLM's packed Slice materialization
and `SparseFlashMlaMetadata`: the latter is a typed AICPU Body dependency with
no AIC/AIV PMU values. It remains inside the Body dependency graph. This is
separate from excluded cross-step controller tails.
