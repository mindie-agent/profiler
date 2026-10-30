# A3 V4Flash caller and BF16 output projection: two-case replay

Only the requested c4/c8 cases were predicted, using fixed Sim `cc245da639ea693daecc3ea273965606659da13a`. Existing controller-corrected observations were reused; no raw event parsing, new collection or unrelated case prediction occurred.

| Case | Primary forwards | Real Body mean ms | Sim ms | Error | Passed layers |
|---|---:|---:|---:|---:|---:|
| v4flash-a3-tp8-c4:q2_b4_m8 | 104 | 32.485961 | 27.638235 | -14.9225% | 20/43 |
| v4flash-a3-tp8-c8:q2_b8_m16 | 104 | 37.763131 | 34.706975 | -8.0930% | 43/43 |

Both primary Body predictions pass. c4 is only 0.025168 ms inside the lower 15% boundary; the unrounded arithmetic is retained. Full extraction still contains 219 forwards across six geometries; the two selected primary populations contain 208 forwards. Four smaller geometries are explicitly deferred, not prediction failures.

The caller now slices TP-local input rows and reconstructs full rows through AllGather; router/shared work remains full-M and expert matrix work is unchanged. MLA grouped_output_a uses the explicitly declared BF16 weight path. This is a conditional whole-Body comparison, not a claim of complete native-contract coverage:

- AllGather remains generic because the captured algorithm is not identified. The neighboring AICPU alternatives were not executed or selected by error.
- The declared catalogue retains three hash-routing and forty generic TopK layers; the capture labels all 43 as Hash. That remaining path difference is explicit.
- The retained c4 TransposeBatchMatMul contract supports BF16 grouped_output_a. The c8 caller evidence lacks that tensor descriptor, so c8 uses the explicitly shared structural precision condition rather than an independently established per-event ABI.
- Layer-0 remains inside Body latency. Steady-layer summaries are separate; no measured wait or residual is subtracted to produce a pass.

[Full Body and layer replay](decode-forward-a3-v4-caller-replay.md), [runtime delta](body-runtime-delta.md), and [independent arithmetic review](body-arithmetic-independent-review.json). Both fresh cost workers completed in under three seconds and below 90 MiB RSS.

[Independent structure audit](structure-condition-independent-review.json): 4,333 checks passed. [Body population and condition audit](body-condition-independent-review.json): 443 checks passed; the original observations, integer endpoints and scenario fields are unchanged, with only explicit source recipe conditions appended.
