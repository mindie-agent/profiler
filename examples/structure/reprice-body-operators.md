# Reprice retained complete-body operator observations

`reprice_body_operator_families.py` reads existing `*.actual.json`, mapping and case evidence. It does not open the source CSV, rerun body segmentation or reuse old predictions. Output belongs to a new comparison arm; existing reports are preserved.

```sh
PYTHONPATH=/path/to/selected-sim-checkout:/path/to/profiler \
python examples/structure/reprice_body_operator_families.py \
  --actual /path/to/old/body-operator-example.actual.json \
  --case /path/to/selected-sim-checkout/examples/cases/example.json \
  --output-dir /path/to/new-operator-arm \
  --variant new-runtime \
  --runtime-source-commit COMMIT \
  --runtime-validation-status maintained
```

Repeat `--actual` to process several sources serially. `--use-source-case-path` uses each actual receipt's original `case_identity.path` as its new declaration, pinning the current bytes. This is useful when every recorded path points into the selected stable checkout. Otherwise pass explicit `--case` for one source or `--case-dir` for declarations sharing a directory. Without a case option, the saved adjacent `.case.json` bytes remain the declared input.

`--validate-only` exports fresh structures and writes the rebind plan without executing costs. `--role router --skip-references` selects a diagnostic program; this deliberately partial report must not replace a full-family scoreboard.

The input join verifies source path/SHA/size, measured q/B and declared context. Cohort counts and activity must fit the retained native-family population. Every prediction then passes Sim's own regenerated graph, tensor contract, physical work, placement and boundary checks.

| Declaration change | Action |
|---|---|
| Graph and declarations unchanged; implementation/rates changed | Use the original mapping identity and execute new physical programs. |
| Same observed contract, semantic candidate IDs, placement and boundary; homogeneous work changed | Generate a new mapping from the fresh manifest, copying only the existing measured aggregate. |
| Candidate set splits into different physical work, or observed contract/semantic boundary changes | Preserve measured population as excluded from this rebind; do not allocate an old histogram among layers. |
| Source-reference program changed | Keep unchanged homogeneous groups as conditional references; list changed groups and their call counts separately. |
| New native ABI required but not retained | Keep unscored. Two examples cannot establish the ABI of every call. Full-ABI rematching is a separate extension, not an implicit behavior of this tool. |

All new work and signatures come from the fresh Sim manifest. Rebinding never only replaces `graph_id`, and a retained source reference never carries its old `physical_work` through a changed program. Partial references report covered, excluded and other-unclassified calls while preserving the full native-family observations and strict accuracy denominator.

To retry failed reference passes after a control-plane memory fix, use `--retry-references-from /path/to/previous/body-operator-family-scoreboard.json --output-dir /path/to/new-reference-arm --variant reference-retry`. This verifies the exact Sim source hashes and original actual/mapping/case/comparison identities, reuses successful strict predictions, and reruns only failed reference passes. The new report retains each `previous_reference_receipt` and references the original strict report. A Sim cost or case change is rejected by this mode and requires a fresh reprice instead. Successful references are retained without another worker. No raw input is read.

The explicit `--frozen-native-rebind` option also revalidates MC2 `DispatchFFNCombine` groups whose original aggregation key retained the complete native ABI. The existing source selector must select the same whole routed-FFN boundary for every saved layer with homogeneous fresh work. The complete original histogram remains one partition; buffer capacity is not treated as observed valid routed rows. Rebound costs remain conditional references, outside strict accuracy. Unsupported ABI groups are still excluded. In reference-retry mode this option also reruns eligible MC2 references that previously completed with excluded work; all previous attempt receipts remain linked and listed.

Each physical program and the reference pass execute in bounded child processes; exceeding 512 MiB fails acceptance explicitly. Full histograms are retained in per-source detail reports. The global scoreboard projects statistics and links those details, avoiding repeated large histogram objects across a multi-source run. Original actual/mapping/case files are referenced by identity rather than copied into new snapshots.

Meaningful regressions use the retained GLM A5 router `[128,4096] × [288,4096] → [128,288]` FP32 capture and V4.1 MQSMLA ratio groups. They cover unchanged observations, uniformly changed work, heterogeneous candidate rejection, changed tensor geometry, cross-capture join rejection, and partial reference coverage. The original 1,302 router calls have mean 19.914667 us; an independently rerun d08 program retained the old 159.681939 us prediction. The owner-candidate implementation in 67ca7673 produces 19.749818 us against the same observations.
