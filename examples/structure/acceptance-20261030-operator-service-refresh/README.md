# Executed operator service refresh — Sim 21c30821

This is an offline replay of retained complete body populations. No raw CSV, device run, model weights, or Body prediction is read to invent an operator cost. Every new cost is executed by Sim Engine through the existing operator/graph/cohort APIs. Calibration values remain explicit in-sample response parameters; their origin does not change strict admission.

## First completed strict sources

| Source | Complete forwards | Strict calls | Compared / passed | Heavy compared / passed |
| --- | ---: | ---: | ---: | ---: |
| Qwen3.5 A5 TP4 c128 | 76 | 41,800 | 13 / 13 | 1 / 1 |
| GLM Flash A3 c4 livepre | 46 | 19,366 | 19 / 18 | 0 / 0 |

Canonical reports are under `qwen35-c128-stable/` and `livepre-c4/`. Independent existing repriced-report checks passed 612 and 832 checks respectively. Qwen coverage is unchanged from the prior canonical report. Its RecurrentGatedDeltaRule (30 calls per forward) executes one observable response per predicted call, at 124.318941 microseconds. Four matrix cohorts also retain actual rule queries. `first-source-coverage-delta.json` records the complete comparison with the previous main inputs.

Livepre's old two HcPost cohorts, 4,140 calls, are temporarily excluded by the existing aggregate rebind guard because the resource boundary changed to a selected native fusion. The original complete normalized contract and candidate IDs remain available; a separate validation is required before these calls can be restored to strict. This decrease is not hidden by a PASS-only report.

## Whole-native conditional execution

`livepre-native-resource/native-service-reference-scoreboard.json` covers both livepre sources, 83 forwards and 22,825 calls in 10 complete native groups. All HCPre/HCPost/GMM-up/GMM-down/SFA boundaries are selected from the fresh full source graph. Fused physical nodes are taken from `resource_operators`, not simulated semantic internals. Actual rule queries establish exactly one joint response per native call. These retained populations have full timing histograms but only source-symbol/partial tensor evidence, so they remain conditional references.

`glm78-native/native-service-reference-scoreboard.json` covers three GLM78 sources, 137 forwards and 51,786 calls in 15 groups. Each source preserves SFA 78, fused GMM-up 75, GMM-down 75, DispatchV2 75 and CombineV2 75 calls per forward. The complete native ABI and integer timing histogram remain intact. Dispatch/combine references contain each complete declared device group; all 75 per-layer physical program sets are executed when their source signatures differ. Three sources use 459 new program sets; peak worker RSS is 469.83 MiB. Capacity and unobserved route/scalar values remain declared conditions, not proven active work.

Each group retains complete calls, Mean/P50, signed activity residual per forward, physical signatures, case/source identity, and `executed_service_response` for every program component. The latter contains actual Engine rule queries, joint service records and provided serviced-work counters. Missing counters are not inferred. Analytical reference work is preserved, but is not charged alongside the joint service. Native activity sums do not add up to Body wall time.

## Execution history and reproducibility

`inputs.json` selects current Body cases in explicit input order. `replay_operator_service_refresh.py` validates each retained actual/mapping/case SHA and invokes the existing complete-family reprice driver. It runs one program worker at a time per queue; two queues cover the remaining six selected sources.

The first Q35 c128 attempt completed its 13 workers but failed the final runtime-identity guard when a concurrent packed-INT8 contract patch landed. Its partial files and failure log are retained under `qwen35-c128/`; they are not accepted current predictions. The stable rerun is separate. The initial livepre-native attempt failed during metadata selection before cost because resource fusion nodes were absent from semantic nodes; its log remains under `livepre-native/`. The corrected resource-aware run is separate.

Focused real-capture tests: `test_operator_service_evidence.py` and `test_native_service_domains.py`, 4 passed. These cover public strict cohort execution, exact service queries, complete retained call populations, and true fusion/V2 ABI boundaries. No historical receipts are rewritten.

The Qwen35 case selection is the explicitly pinned pre-shared-native Body generation. A later BF16 shared-expert Body declaration landed while this queue was running; it is not silently substituted into these operator receipts. Body and operator case identities remain separate, and the changed shared-expert families need a scoped fresh rebind.

## Completed selection

`completed-inputs.json` lists the eight complete canonical receipts after the HcPost repair: **132/136 strict cohorts, 214,818 calls across 445 forwards**; micro 128/132 and heavy 4/4. The four HC sources now preserve their original strict populations. `complete-hcpost/` retains the exact contract/member proofs and fresh full-source Engine execution; no old costs were copied. The six initial conservative receipts remain as history under `canonical/`.

For current native reference import use `livepre-native-resource/current-native-reference-scoreboard.json`: its eight groups contain 15,355 calls, omitting 7,470 HcPost calls already strictly scored. The complete original ten-group execution receipt is unchanged. Keep GLM78 fifteen groups as references. Supersede prior references only for the same source/geometry/native/layer population; preserve other families such as KDA. Different historical source-symbol IDs are not evidence of disjoint measurements.
