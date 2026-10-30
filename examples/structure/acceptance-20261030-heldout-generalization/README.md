# Retrospective leave-concurrency-out: GLMFlash A5 TP8

Training sources: c1, c8/p4k, c32/p4k. Validation excludes all three training source SHA values. The nonnegative fixed-plus-one-physical-axis function was frozen before validation. All earlier per-point service responses were removed from the six validation inputs.

This is **retrospective operator-only fit exclusion**. Body replay is a counterfactual on historically developed source/hardware programs, not a claim of prospective whole-model blindness. Both `heldout_engine_20261030` directories were empty. No new capture or raw scan.

25 physical domains; 150 validation groups: **144 pass**, including all micro groups. Six heavy failures are grouped up/down at M64 (two sources) and extrapolated M256. The model was not refit after these failures. Context-dependent MLA/indexer/metadata and two incomplete training Slice domains remain analytic.

| Held-out source | Real Body ms | Sim ms | Error | ≤15% |
|---|---:|---:|---:|---|
| a5_glm53flash_tp8_c64_p4k | 46.528233 | 55.427467 | +19.13% | FAIL |
| a5_glm53flash_tp8_c32_p8k | 38.713189 | 35.597357 | -8.05% | PASS |
| a5_glm53flash_tp8_c16_p4k | 33.030918 | 26.584468 | -19.52% | FAIL |
| a5_glm53flash_tp8_c16_p8k | 33.616091 | 26.771901 | -20.36% | FAIL |
| a5_glm53flash_tp8_c4_p8k | 21.418246 | 17.579151 | -17.92% | FAIL |
| glm53flash-a5-tp8-c3 | 21.067549 | 18.023566 | -14.45% | PASS |

Body: **2/6 pass**, 17 smaller geometry groups remain measured and deferred. Full source population is 228 accepted forwards over 23 geometry groups. Operator pass rates do not imply Body accuracy.

Parameter review: 1,644 checks; Body review: 1,217 checks; zero failures. The review certifies training-source exclusion, NNLS KKT conditions, complete native multiplicities, actual saved rule hit counts and unrounded accuracy. It does not certify hidden binary tiling or historically unseen source programs.

Reproduce (fixed Sim `21c30821` on `PYTHONPATH`, profiler checkout working directory):

```sh
python examples/structure/retrospective_heldout_service.py register
python examples/structure/retrospective_heldout_service.py fit
python examples/structure/retrospective_heldout_service.py evaluate
python examples/structure/replay_decode_forwards.py --manifest examples/structure/acceptance-20261030-heldout-generalization/decode-forward-heldout-cases.json --output examples/structure/acceptance-20261030-heldout-generalization/decode-forward-heldout-replay.json --geometry-limit 1 --prediction-timeout 90 --runtime-source-commit 21c30821d87a757bace8cf6b2fffea2536db643e
python examples/structure/review_retrospective_heldout.py examples/structure/acceptance-20261030-heldout-generalization
```

The replay JSON uses compact JSON formatting only; all saved fields are retained (3.43 MB). Parameters and source pins are in `split-policy.json` and `training-models.json`. No case or threshold was chosen according to the validation errors.
