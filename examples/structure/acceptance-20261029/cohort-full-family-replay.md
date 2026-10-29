# Complete family and physical-cohort replay

This is the latest cohort replay for 2026-10-29. It reuses eight complete A3/A5
captures containing **668,835 positive-duration events and 148 native types**.
There are nine phase declarations and thirteen declaration/resource variants.
Kimi prefill/decode reuse one capture; variants are not independent hardware
evidence. No new NPU workload was launched.

The runner no longer has `COMPARE_TYPES`. Every eligible cohort enters
`compare_cohorts`. All 148 native types remain in the family tables, including
types with no valid tensor/physical-work cohort. Each physical program has an
independent 120-second budget, so one slow prediction cannot discard other
results. All programs completed in this run.

## Results and comparison boundaries

| Capture / declaration | Raw events | Cohort events | Compared / reference cohorts |
| --- | ---: | ---: | --- |
| A3 GLM53 prefill, unfused reference | 2,392 | 1,076 | 16 / 6 |
| A3 GLM53 prefill, selected fusion | 2,392 | 1,076 | 19 / 3 |
| A3 GLM53 decode, unfused reference | 166,204 | 79,624 | 16 / 6 |
| A3 GLM53 decode, selected fusion | 166,204 | 79,624 | 19 / 3 |
| A3 Qwen35 | 121,802 | 3,442 | 14 / 1 |
| A3 Qwen36 | 40,628 | 1,292 | 14 / 0 |
| A3 V4 Flash, default | 4,064 | 684 | 13 / 3 |
| A3 V4 Flash, selected fusion | 4,064 | 684 | 14 / 2 |
| A3 V4 Pro, default | 24,271 | 4,336 | 14 / 3 |
| A3 V4 Pro, selected fusion | 24,271 | 4,336 | 15 / 2 |
| A5 Kimi K3, prefill declaration | 286,988 | 0 | 0 / 0 |
| A5 Kimi K3, decode declaration | same capture | 0 | 0 / 0 |
| A5 Qwen38 | 22,486 | 989 | 22 / 0 |

Across the thirteen variants, **176 cohort comparisons and 29 references**
complete, with no failed programs. These totals include repeated declarations.
Taking the primary reference/default once per capture yields 91,443 cohort
events: 63,446 scored and 27,997 reference events. Selecting the native-fusion
variants for the four GLM/V4 captures instead yields 71,455 scored and 19,988
reference events over the same cohort-event set.

Thirty-three native types produce cohorts; thirty have at least one scored
comparison. Eight have reference results, overlapping the scored set. The other
115 types remain visible with their evidence or capability gaps. There are
**zero inferred layer bindings**. Event counts do not establish step counts.
Complete captures can contain phases and geometries outside the selected case.

The [complete Top family/subgraph table](fusion-cohort-replay-top-errors.md)
shows full event/activity denominators and scored subsets. Its
[JSON index](fusion-cohort-replay-families.json) links all thirteen complete
family tables. Activity sums include overlapping events and are not model
wall-clock time.

The [fusion coverage inventory](fusion-coverage-inventory.md) separates default
cases from the exact source-selected cases saved by this replay. Its
[JSON inventory](fusion-coverage-inventory.json) retains all 148 types and
per-capture reasons. Of 59 required model-body types, 47 have a declared native
boundary, 45 have a complete boundary, 33 have a comparable contract, and 31
match at least one retained original fixture row. A declared boundary or a
fixture match does not establish a captured layer occurrence.

## Head contracts and remaining gaps

- V3 now checks the real A3 INT8 and A5 MXFP8 branches separately. V4 checks the
  retained FP8/FP4 five-slot interface, scale ordering and NZ axes. GroupedMatmul
  preserves expert-bank geometry instead of becoming a dense GEMM.
- AddRmsNormBias and AddRmsNormDynamicQuant use explicit source-selected norm
  resources, including beta work and materialized outputs. The independent
  [checkpoint/source evidence](head-normalization-evidence.md) explains GLM's
  global norm-bias allocation rule.
- MoeGatingTopK/Hash have declared selection subgraphs, separate from the router
  GEMM. An unselected multi-program boundary remains a reference.
- RmsNormDynamicMxQuant and SituMxQuant have active contracts and explicit
  resource paths. Kimi's latent norm now follows combine and precedes latent-up,
  with gamma traffic included. Its retained case still differs from the capture
  precision/placement/work conditions; no observation was used to rewrite it.
- W4A8 GroupedMatmul's correction/rescale epilogue remains unmodeled. Its cohort
  retains statistics and a partial prediction, but gets
  `reference_only / quantized_epilogue_unmodeled`.
- MoeInitRoutingV3 and MoeTokenUnpermute remain native declarations without a
  supported active tensor contract in these cases. Their absence from scored
  rows is now visible as a contract gap, not hidden by a comparison allowlist.

Predictions still have material errors. GLM prefill SparseFlashAttention is
53.63% below measured activity; GLM decode is 97.81% below. A5 Qwen38 V3 matrix
cohorts aggregate to 75.47% above their scored measured activity. These are
conditional comparisons, not evidence of successful end-to-end accuracy or
captured dispatch identification.

## Verification

The [full replay validation](fusion-cohort-validation.json) records unchanged
runtime hashes, unchanged capture identities and **417.373 seconds** elapsed.
Peak mapping-worker RSS is **419,987,456 bytes (400.53 MiB)**; peak comparison RSS
is **386,334,720 bytes (368.44 MiB)**, both below 512 MiB. Nine serial capture scans
keep the two Kimi declarations within this budget.

The [independent review](fusion-cohort-independent-review.json) recomputes
117 cohort distributions from four original captures (331,026 events), and
checks all thirteen family denominators and error equations.
[Maintained-suite verification](cohort-verification.json) records the same
runtime-source hash: profiler **517 passed, 26 skipped**; sim **1,351 passed**.
Skipped live tests and historical replay are not new hardware acceptance.

Replay and all thirteen fresh inventory graph checks used **CPython 3.13.12**
at `/Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python`. Reproduction uses
the same interpreter version and the companion development sources:

```bash
PYTHONPATH=/path/to/sim-rewrite:/path/to/profiler /path/to/sim-rewrite/.venv/bin/python \
  examples/structure/replay_fusion_cohorts.py --run
```

`--compare-existing --run` reuses saved mappings and case artifacts, but still
requires the case to regenerate the same graph identity. Changed declarations
must be remapped.

A separate cross-version check found a real routing/shape sensitivity, not
only a hash-format difference. `RoutingPolicy.local` for the V4 Pro uniform
384-expert, top-6, EP16, 1,024-token declaration returns
`384.00000000000045` expected rows on CPython 3.11.13 and
`383.99999999999653` on 3.13.12. The downstream `ceil` consequently declares
385 versus 384 matrix/quantization rows. The final reports and inventory
reproduce the 3.13.12 graphs; they do not attest cross-version graph identity.
This issue is recorded separately and was not repaired by changing captures
or saved case declarations.
