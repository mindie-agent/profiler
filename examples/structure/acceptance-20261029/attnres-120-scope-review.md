# AttnRes 120-call scope review

Reviewed on 2026-10-30 against final clean isolated sim commit
`26f5adb48dd418584cd18c79d6a63ca8ab42afd7` and profiler
`902359fafeb0d08d4e8fdefa389a99681928932f`.
The AttnRes family, subgraph contracts, conditional case and operator document
match the initially reviewed `01be0d99` byte for byte. Committed blobs and the
isolated checkout were both checked; no raw rescan or prediction rerun was needed.

The requested **120 AttnResFwd calls are not located in the retained evidence
inspected**. No capture identity, window, stream or event-row selection establishing
that population was found. Its count is therefore unverified, and no 120-call
accuracy result is produced. The companion JSON records the inspected artifacts
and their SHA256 values.

## Checked populations

The historical full-capture inventory has 14,768 AttnResFwd events in four
descriptor classes. Its source is
`/Volumes/data-tmp/tmp/mindie-body-profiling-kimi-op-summary.csv`, SHA256
`ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648`.
This review did not rescan that 110 MB file.

| Recorded main-output extent | Events | Original descriptor counts | Activity |
| --- | ---: | --- | ---: |
| 7,340,032 BF16 elements | 748 | 4 + 744 | 97.622454 ms |
| 7,168 BF16 elements | 14,020 | 75 + 13,945 | 147.965865 ms |

These are recorded extent classes, not independently observed phase, step or
layer labels. Neither population substitutes for the requested 120 calls.
The old 187-points-per-forward declaration and its hypothetical four-forward
total of 748 remain reference-only. The latest model scoreboard explicitly
labels that comparison conditional and excludes it from scored cohorts.

The inspected Kimi KDA call-block report contains 276 source-compatible
four-stage ChunkKDA blocks. Its AttnRes entries are neighboring event examples;
they do not establish a 120-call AttnRes window.

## Source binding remains incomplete

The final committed AttnRes family, case and structure-contract code are
unchanged from `2c0b339a` for the paths checked. The source-selected
`attn_res_prefix_point` exposes a complete caller declaration: prefix and bank
identities, active tokens, valid blocks, optional add, normalization, write slot,
materialization and prefill optimization. These are declared inputs, not
per-event observations.

The retained image
`883670fcc91cbd75a7070b00501be0ecd81a266b81366a21bf02139d8e6a33e1`
provides the matching six-input/three-BF16-output interface. In
`tests/fixtures/kimi_grouped_attnres/source_image_883670fc/attn_res_fwd_common.h:45`,
missing optional add and output-normalization tensors use nonempty fallbacks.
Their recorded presence cannot reveal the corresponding scalar flags.
Flattened backing allocations also omit active prefix shape, bank stride and
history depth. Equal descriptors can consequently cover different physical work.

All four retained real rows still return `observed_contract=None` with
`active_view_or_stride_unobserved`. The source implementation correspondence
remains available; tensor candidates, occurrence binding and scored comparison
do not follow from that correspondence.

## Reproducible scope tool

`/Users/maoxx241/code/profiler/examples/structure/replay_attnres_scope.py` verifies
the source SHA256 and accepts exactly one caller-supplied scope: a nanosecond
window, CSV row locators, or an explicitly requested complete capture.
Device and stream filters are optional. Expected count is an assertion after
selection; a mismatch writes `status=count_mismatch` and exits 1. It never
selects the first 120 events or derives flags from duration.

The tool preserves complete versus clipped counts and intersection activity.
It retains bounded descriptor aggregates and one event identity per descriptor.
It performs no sim export, prediction, layer binding or flag inference.

The four-row retained example can be checked without reading the large capture:

```sh
PYTHONPATH=/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  /Users/maoxx241/code/profiler/examples/structure/replay_attnres_scope.py \
  /Users/maoxx241/code/profiler/tests/fixtures/kimi_grouped_attnres/a5_kimi_k3.csv \
  --source-sha256 7b3f0cdf5bf2f318cfbdd3a5df4d95dc2e55092ed7ee2ed161106b534951bd16 \
  --complete-capture --expected-events 4 \
  --output /tmp/P2-attnres-retained-fixture-scope-20261030.json
```

That result counts four retained examples, not the full-capture descriptor
frequencies. The focused tests pass: **3 passed in 0.06s**, covering real-window
accounting, a rejected 120-count assertion on a clipped two-event window, and
unchanged descriptor/flag conclusions after duration perturbation.

A real 120-call revalidation requires its source identity and an explicit
window or event locator. Scored source-program comparison additionally requires
the missing active views and scalar dispatch conditions to be observed or
independently bound; caller-only assumptions remain reference-only.
