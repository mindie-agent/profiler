# High-concurrency priority replay

The main scoreboard now contains the eight accepted source-arm cases and six
priority A5 cases. The overlapping selections contain 13 sources and 877
selected complete Forwards; neither table adds captures to the main denominator.
Execution completion, Body accuracy and native contract coverage are separate.

The current focus has 13/13 Body PASS, including all six A5 priority cases.
The main board has 62/66 PASS over 5,250 distinct observed Forwards, with all
66 latest predictions completed. Kimi low-concurrency c1/c2/c4/c8 now contributes
eight new PASS results. A subsequent replay uses the source force-EPLB policy
to close the declared expert-routing work discrepancy while retaining all eight
PASS results. Captured group-list values remain unobserved. Qwen3.5 TP4
c4/c64/c128 now pass at -14.66%/-14.28%/-13.56%. A3 GLM
c4-livepre also passes after its native source declaration. GLM78 c8's earlier
PASS is superseded by the latest complete caller replay (+18.00%, FAIL).

GLM uses the corrected HC native implementation consistently across all nine
A5 cases. Complete matrix, norm/quant and native HC response populations, then
eleven layer-ordered AICPU sparse-attention metadata calls, bring all nine to
PASS. The earlier 3/9 source-corrected result and the preceding 6/9 result whose
decomposed HC work compensated for missing costs stay inspectable. Remaining
failures are the three A3 GLM78 sources and A3 GLM Flash c16-livepre. GLM78's
complete local padding, AllGather, router precision and consumer-scoped norm
declaration brings the two c2 cases to -15.41%/-15.65%. Native MC2 still needs
to replace generic pack/transport/quant boundaries; complete-body accuracy
does not override this recorded source mismatch.

`source-inventory.json` records selection identities, benchmark scenarios and the
state before this replay. Its old predictions are not inputs to the focus table.
`high-concurrency-scoreboard.json` reads current selected Body rows from the main
scoreboard, joined by exact case and source SHA. Latest failed attempts remain
visible even when an earlier completed prediction is retained.

The initial four MC2 baseline cases were predicted using `cc245da6`, whose runtime tree is
identical to `8eda7e91` / `ab37ffe5`. Their retained measurements were reused;
no new capture parsing or device work ran. Qwen3.6 c96 and GLM c64 retained their
existing results because their selected physical programs were unchanged.

| Case | Forwards | Real Mean ms | Sim ms | Error |
|---|---:|---:|---:|---:|
| Kimi c32 p4k | 46 | 40.018728 | 28.543890 | -28.67% |
| Kimi c32 p16k | 41 | 44.666193 | 33.730644 | -24.48% |
| V4.1 c64 | 75 | 26.328226 | 18.932611 | -28.09% |
| V4.1 c128 | 73 | 27.285973 | 19.245008 | -29.47% |

All four executions completed; none met the unchanged 15% Body tolerance.
The MC2 prefix update changed these Body predictions by less than 0.3 us each.
The largest worker used 449.94 MiB. The independent receipt review checked
3,880 identities and arithmetic invariants without failures.

The cc245da6 baseline main board had 23/66 Body PASS before observable-response arms. A3 V4Flash c4/c8 are PASS at
-14.92%/-8.09%. Qwen3.6 TP2 c96 is still -15.514%, 0.328251 ms outside the
15% band; this distance is not a physical service budget to add to the model.

Observable small-payload / low-M rates and per-call / per-group service
parameters are accepted through the same comparison path. Explicit calibration
metadata is retained separately from accuracy. In-sample results are admitted;
unreported data independence is `not_declared`, not invented held-out evidence.

Validation: 850 tests passed, 26 optional tests skipped. The full-suite controller
review initially exceeded the RSS gate while retaining two full comparison
graphs; the test now keeps a compact baseline projection and streams JSON.
The unchanged 512 MiB gate passes. The current main-board independent review
is rerun after each integration. Sharing identical immutable
receipt metadata reduced review memory from 465.3 MiB without dropping fields.
The 25 affected scoreboard tests
also pass, including concurrent readers seeing a complete prior JSON while the
new report is published atomically.

Rebuild the current focus table after any affected-case replay is added to the
ordered main manifest:

```sh
PYTHONPATH=. python examples/structure/priority_decode_scoreboard.py \
  --input-manifest examples/structure/acceptance-20261030-priority/priority-scoreboard-inputs.json \
  --output examples/structure/acceptance-20261030-priority/priority-three-level-scoreboard.json
PYTHONPATH=. python examples/structure/high_concurrency_scoreboard.py \
  --scoreboard examples/structure/acceptance-20261030-priority/priority-three-level-scoreboard.json \
  --focus-spec examples/structure/acceptance-20261030-high-concurrency-priority/source-inventory.json \
  --output examples/structure/acceptance-20261030-high-concurrency-priority/high-concurrency-scoreboard.json
```
