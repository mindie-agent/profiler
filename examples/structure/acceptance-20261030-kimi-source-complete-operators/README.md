# Kimi source-complete canonical cohorts

This arm reuses 12 retained A5 BF16 captures, 618 complete Body Forward instances,
and 3,348,783 selected device events. No profiling CSV was parsed and no hardware
collection was started. Runtime is committed Sim
`30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`; each input is the corresponding
`kimi-source-complete/*_source_complete.json` case pinned by
`../acceptance-20261030-source-complete/decode-forward-kimi-cases.json`.

The authoritative complete-family receipt is
[`full-matrix-canonical/body-operator-family-scoreboard.json`](full-matrix-canonical/body-operator-family-scoreboard.json).
It preserves all families and refreshes complete retained MatMul ABI/topology
partitions against fresh declarations. It records **361,732 strict events,
122/122 passing cohorts: 118/118 at ≤50 us with ≤15 us absolute tolerance and
4/4 above 50 us with ≤15% relative tolerance**. These are covered cohorts, not
a claim that the entire Body or all native families meet their accuracy targets.

The initial full-family repricing is retained at
[`body-operator-family-scoreboard.json`](body-operator-family-scoreboard.json):
102/102 passing cohorts and 314,746 strict events. It used fresh costs, completed
in 228.99 s, and kept all original native duration histograms. Full MatMul
candidate reconstruction then added 46,986 scored events, chiefly the newly
declared active-row projections at B1/B2/B4. This second phase used 14 new
physical programs and reused 90 MatMul cohort costs only when the Sim source
identity and physical program key agreed. It took 42.87 s with a 396.2 MiB peak.
All non-MatMul families and their costs remain in the canonical receipt.

The first reconstruction invocation failed before any output or cost because
the original matrix-only partition schema carries its native kind in the full
ABI rather than a separate `native_operator_type` field. The reader now accepts
that original schema; the complete-population regression test verifies every
histogram bin. The corrected successful invocation is the recorded canonical
generation. The prior full-family cost generation is retained separately.

Input lineage is explicit: original actual, previous actual, full native
partition, source capture, accepted Body windows and geometry must join.
Equal-work alternatives remain one candidate-set cohort; this does not invent
a Host occurrence or allocate measured duration to individual semantic roles.
The companion seven-family conditional references are in
[`../acceptance-20261030-kimi-source-complete-references/`](../acceptance-20261030-kimi-source-complete-references/).

To reproduce, run `reprice_body_operator_families.py` once per source with the
retained actual/mapping and explicit source-complete case; combine its compact
case indices as this initial receipt does. Then run
`reprice_kimi_matrix_partitions.py --previous <initial-receipt>
--partition-dir examples/structure/acceptance-20261030-matrix-fix
--output-dir <new-arm>/full-matrix-canonical --variant <new-arm-name>`.
Use the pinned Sim commit on `PYTHONPATH`; never substitute a moving runtime.
