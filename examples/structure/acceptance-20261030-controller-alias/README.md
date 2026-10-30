# Typed AICPU controller alias repair

The production predicate is now `is_aicpu_controller(event)`: both the recorded
core/task type and one of the four already-supported controller names must
match. Case and underscore spelling differences are canonicalized. A
`COMMUNICATION` HCOM envelope such as `hcom_allReduce_AicpuKernel` remains data
plane evidence; a name suffix alone never removes an event.

The existing boundary policy is unchanged: a typed controller must cross an
actual successor input boundary before its suffix is excluded. Internal device
communication remains intact. Controller intervals do not contribute to the
non-controller device activity union; an in-scope controller completion may
still determine the span when there is no cross-boundary evidence.

## Complete local replay

[Final summary](controller-alias-summary.json) and
[extraction-generation map](extraction-generation-map.json) cover all **66
captures, 5,250 complete Body forwards and 222 geometry buckets**. The final
unique-source streams parsed **12,706,254 events**. Each source reuses the exact
model configuration from the pinned HCCL input manifest, without weights,
remote collection, device initialization or Sim predictions.

| Check | Result |
| --- | ---: |
| Body endpoint changes | 0 |
| Layer input/start changes | 0 |
| Layer end changes | 3,027 |
| Body activity-union changes with a prior value | 1,562 |
| Historical forwards without activity metrics | 409 |
| Independently paired complete layer scopes | 233,074 |
| Newly recognized typed controller aliases inside Body | 24,806 |
| Sources whose strict/native operator population can be retained | 66 / 66 |
| Summary identity/population/arithmetic checks | 16,744 passed |
| Maximum reported successful worker RSS | 311.36 MiB |

The 409 historical missing activity values remain **unavailable**, not zero or
an unchanged measurement. Their newly emitted activity/gap values are separate
from measured before/after deltas.

The five A3 Kimi four-layer sources and five A3 V4.1 DSpark7 sources account for
the alias changes. The source comparison JSON records each changed scope's
old/new integer endpoints or union, associated forward and layer, and actual
first/last/successor locators. A same-stream observer evaluates the frozen old
exact-name predicate on the same raw scope solely as a regression oracle; it
is not a production fallback or a second raw scan.

`BodyConsumer` assigns native events using Body endpoints, layer starts and raw
norm/attention-anchor FFN partitions. It does not use a layer's last controller
completion to assign an event. All those population boundaries remain intact,
so a corrected layer end does **not** invalidate existing strict/native
histograms. The final summary's `body_operator_population_reusable` reflects
that consumer contract; the intermediate `scope-paired` comparison field
`operator_population_reusable` was the stricter all-scope-endpoints check and
must not be used as the final reuse decision.

## Controller population projection

[Operator population audit](operator-population-review.json) verifies 10
retained actual populations across 30 historical operator-report occurrences,
with **460 checks and no failure**. Complete duration histograms match the
same-source, same-geometry HCCL ledger, whose records are typed `AI_CPU`.
These legacy `reduce_scatterAicpuKernel` rows have zero strict cohorts and zero
conditional resource programs. Their exact original report SHA, case ID,
family index, actual SHA, source SHA, geometry, count and elapsed activity are
retained for an explicit `controller_overlay` projection. Original costs and
histories are not rewritten; strict/reference accuracy denominators do not
change. Controller elapsed is not an unmodeled physical-service residual and
does not prove link service or peer-wait causality.

## Execution history and recovery

- The initial [receipt](decode-forward-auto-acceptance.json) records 8 streams:
  3 completed and 5 metadata-accounting failures because older extraction
  schemas lacked activity fields. Those failures were not parser failures.
- The [paired-scope receipt](scope-paired/decode-forward-auto-acceptance.json)
  records 43 streams: 37 completed and 6 metadata-accounting failures because
  hidden-output models close at terminal normalization and have no vocabulary
  head. Their successfully written extractions remain preserved.
- The [completed receipt](completed/decode-forward-auto-acceptance.json)
  reuses the 37 successful extractions and executes 29 remaining/recovery
  streams. Hidden-output occurrences are paired by device and measured Body
  input boundary; head-bearing models use the vocabulary-head occurrence.

There were **80 full source-stream attempts** in this repair, plus one bounded
c32 source read to retain the actual 180-row regression fixture. The 66 final
source populations are counted once. Different accounting-runner generations
retain their individual identities; the canonical controller core bytes stayed
identical throughout. The two failed receipts are deliberately preserved and
are not relabeled completed.

The c32 fixture comes unchanged from original CSV lines 9,521–9,700. Its
6.646987 ms Body span is unchanged; its data-plane union changes from 6.552030
to 6.519291 ms. The eight underscore aliases account for the removed 32.739 us
of interval coverage, without deleting the real HCOM intervals. Focused
controller, automatic-boundary, mHC, operator-consumer and HCCL regression tests:
**33 passed**.

Reproduce the summary without reading raw captures or predicting costs:

```sh
python3 examples/structure/summarize_controller_alias_replay.py \
  --receipt examples/structure/acceptance-20261030-controller-alias/completed/decode-forward-auto-acceptance.json \
  --inputs examples/structure/acceptance-20261030-hccl-66/inputs.json \
  --output-dir examples/structure/acceptance-20261030-controller-alias
```
