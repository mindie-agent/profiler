# Source caller, routing cohort and explicit HCCL replay

This acceptance reuses existing A5 captures with Sim runtime `40e4300ea7ccc1123759f6201cc2d69e3aa77ad6`. No device workload was launched. The six inputs comprise Qwen3.6 TP2 c1/c12/c96 (164 selected complete Forwards) and GLM Flash TP8 c16/c32/c64 (92 Forwards). Client concurrency and measured execution geometry remain separate fields in the inputs.

## Current inputs for the unified scoreboard

- `source-caller-current-reference-scoreboard.json`: 21 conditional groups, 27,248 calls. This contains 18 HCCL groups (20,992 calls) and three pooled convolution-state-copy groups (6,256 calls).
- `routing-operator-supplement.json`: three strict `MoeInitRoutingV3` cohorts, 3,864 calls across 42 identical-work layers per source. Apply through `operator_supplements`, never as a whole-source operator replacement.
- `../acceptance-20261030-controller-alias/operator-population-review.json`: audited AI_CPU populations for `controller_overlays`. The display moves these exact populations out of physical-service gap rankings while preserving original event and strict denominators.

The historical `source-caller-reference-scoreboard.json` preserves all 27 initially priced groups and 31,112 calls. Its six routing reference groups are superseded by the three strict routing cohorts. The current projection records their exact full-histogram correspondence and the superseding receipt; it performs no new pricing. Historical and current reference coverage must not be added together.

## Evidence and boundaries

`_copy_conv_state_kernel` has N/A tensor descriptors in the actual capture. The Sim caller supplies two explicit `triton_noncontiguous_conv_state_copy` programs per KDA layer, with six state slots. The retained 68 calls per Forward exactly cover 34 layers × gather/scatter. Their directions remain pooled: reference cost per observed call is `(gather + scatter) / 2`. No particular event is assigned a direction. Zero-fill and causal convolution are separate programs and excluded. All participating layer work is checked for equality. This remains a source-symbol reference, not a native-ABI cohort.

Routing first had only two retained raw examples, which were insufficient to claim population-wide ABI equality. A necessary targeted streaming pass over each of the three existing CSVs collected every `MoeInitRoutingV3` inside the already accepted Body windows. All 3,864 events retain the complete two-input/four-output ABI and exact original duration histogram. Input BF16 activations and INT32 expert IDs, FP8 E4M3 output, INT32 row indices, INT64 expert counts and E8M0 scales all match the exported active routing contract. Existing cohort matching then verifies equal physical work and placement across the 42 candidate layers. It does not claim Host-based layer occurrence, expert-ID values, sort flags or captured source-binary identity.

| GLM source | Calls | Real Mean / P50 us | Sim us/call | Difference us | Tier |
| --- | ---: | ---: | ---: | ---: | --- |
| c16 | 1,260 | 23.010918 / 23.051500 | 1.312000 | -21.698918 | micro: fail |
| c32 | 1,302 | 24.684824 / 24.843500 | 1.755819 | -22.929005 | micro: fail |
| c64 | 1,302 | 28.767924 / 28.822000 | 3.275354 | -25.492570 | micro: fail |

The full routing contract unlocks scoring, but all three predictions miss the 15 us tolerance. These are measured cost discrepancies, not evidence gaps or successful calibration.

HCCL references consume the complete explicit source collective: entry, every local phase, peer exchange and exit. Layer 0 is retained separately, with its actual full histogram. The observed Qwen population is `AivKernel`; an AICPU_TS declaration is rejected for that observed engine. Kernel names alone do not establish selected template, payload, reduction arguments or peer readiness. The present real cost acceptance covers AIV allReduce. The mapper also recognizes explicit allGather/reduceScatter source families, but this batch does not claim a real AICPU_TS allGather/reduceScatter acceptance. Qwen3.5 AIV allGather is not substituted with a different engine.

All reference residuals compare event activity with source program service. They cannot be added to explain Body wall-clock error. Unlinked AICPU controllers and exactly duplicated HCOM summaries are not added to device activity.

## Reproduction and execution

`source-caller-inputs.json` pins retained source/Body artifacts and case bytes. The Qwen cases are the parent-provided explicit HCCL declarations. The three GLM cases are local acceptance overlays changing only the copy/routing lowering selections; model, machine and parallel placement are checked against the original retained case.

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/compare_source_caller_references.py \
  --inputs examples/structure/acceptance-20261030-source-callers-40e4300e/source-caller-inputs.json \
  --output-dir examples/structure/acceptance-20261030-source-callers-40e4300e \
  --runtime-source-commit 40e4300ea7ccc1123759f6201cc2d69e3aa77ad6

python3 examples/structure/operator_family_supplements.py \
  --references examples/structure/acceptance-20261030-source-callers-40e4300e/source-caller-reference-scoreboard.json \
  --supplement examples/structure/acceptance-20261030-source-callers-40e4300e/routing-operator-supplement.json \
  --output examples/structure/acceptance-20261030-source-callers-40e4300e/source-caller-current-reference-scoreboard.json
```

The final six-source reference batch took 5.251 seconds, with peak RSS 148.66 MiB and zero raw capture reads. It is a final rerun after completing importer fields; earlier development cost executions are not additional measured population. The three necessary routing scans took 15.547 seconds in total, at most 160.41 MiB, and are recorded separately in `routing-native/native-partition-receipt.json`. The first routing trial completed its comparison but hit a CLI summary-print KeyError; this was fixed and all three final comparisons were rerun. The completed final receipts and logs preserve the final actual executions.

Regression coverage uses captured N/A copy rows, full four-output routing ABI, actual whole HCCL programs, exact histogram conservation, family-scoped replacement, duplicate supplement handling, and missing-controller-overlay detection. No fixture fabricates a Host stack or assigns latency-derived roles.
