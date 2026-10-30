# GLM78 indexer and routing native services

This increment retains the complete typed V2 caller and every prior response rule. It enables the existing `lightning_indexer` and `router_selection` fusion regions, then binds their complete same-source native observations to one local joint service per fused call. No Sim implementation or acceptance threshold changes.

| Source | Real Body mean ms | Sim ms | Error | Passed layers |
|---|---:|---:|---:|---:|
| tpot30 c2 | 57.639270 | 49.468163 | −14.1763% | 37/78 |
| tpot50 c2 | 57.817112 | 49.442825 | −14.4841% | 33/78 |
| tpot88 c8 | 69.556298 | 66.914718 | −3.7978% | 78/78 |

All three Body comparisons pass the unchanged 15% criterion; the two c2 cases still exceed the new 10% refinement goal. The preceding V2 arm's tpot50 failure remains immutable. Source coverage stays 162 Forwards in ten geometry groups: 137 primary Forwards are compared, and seven other groups remain explicitly deferred. Three fresh predictions complete in 16.60 seconds. No raw capture or device work is repeated.

Fresh graph contracts and the complete observed native ABI agree for 21 LightningIndexer and 75 MoeGatingTopK calls per Forward. The indexer population is only the 21 DSA layers. The remaining 57 attention layers receive no indexer rule. The optional indexer output and TopK's third FP32 score output remain recorded in the full ABI; the active contracts identify the complete providers, without establishing internal tiling, pointer aliasing or Host occurrence binding. Strict cohort admission is unchanged.

Each complete arithmetic mean becomes one inclusive local `joint_native_a3` service, replacing that fused region's analytic schedule while preserving analytical work as reference. The prior SFA/GMM joint invocations remain 78/75/75, and the V2 communication group floors remain 75/75. This is in-sample observed service calibration. Native activity differences are not summed as a Body wall attribution. Existing unknown logical transport concurrency and all-rank symmetry conditions remain visible.

The Sim pin is `21c30821d87a757bace8cf6b2fffea2536db643e` (runtime code unchanged from f6e68d5e). The builder, source identities, full integer histograms, exact active contracts and new physical selectors are saved in `tail-native-input-proof.json`. The standard Body review passes 999 checks; the independent parameter and invocation review passes 112 checks.

Reproduce from the profiler checkout using the pinned Sim checkout:

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/build_glm78_tail_service_cases.py
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-a3-tail-service-refinement/glm78-indexer-routing/decode-forward-glm78-tail-cases.json \
  --output examples/structure/acceptance-20261030-a3-tail-service-refinement/glm78-indexer-routing/decode-forward-glm78-tail-replay.json \
  --geometry-limit 1 --prediction-timeout 90 \
  --runtime-source-commit 21c30821d87a757bace8cf6b2fffea2536db643e
```
