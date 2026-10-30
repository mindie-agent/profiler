# Qwen3.5 A5 TP4 native-domain refinement

This is a local replay of three existing captures using Sim `21c30821d87a757bace8cf6b2fffea2536db643e` (package SHA `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`). It is explicitly **in-sample observed-service calibration**, not a new device run or strict native-contract coverage claim.

| Client case | Selected forwards | Real mean ms | Sim ms | Error | ≤15% | ≤8% |
|---|---:|---:|---:|---:|---|---|
| c4 control | 84 | 11.551367 | 9.857738 | −14.6617% | pass | fail |
| c64 | 79 | 21.956845 | 19.838785 | −9.6465% | pass | fail |
| c128 | 76 | 28.584774 | 25.902670 | −9.3830% | pass | fail |

The report retains all 286 accepted forwards across 40 geometries. Cost comparison selects 239 forwards in the three main geometries; the remaining 37 geometries are explicitly deferred. Each high-batch case adds 13 source responses and replaces the two prior grouped-matrix responses with its own complete native means. No c4 latency is copied to a larger batch. The unchanged c4 control retains one unmatched legacy small-row DSQ rule; its separate applicable response remains present.

`observed-populations.json` retains complete integer duration histograms, active tensor cohort evidence, and conditional source-role evidence separately. GDN Q/K L2 helpers share the complete 60-call histogram and pooled per-call mean, each applied to 30 physical calls; they do not each receive the total 60-call duration. Grouped buffer capacity does not establish routed valid rows. FIA full timing is paired with retained ABI examples and source geometry, not advertised as full native ABI validation.

`decode-forward-replay.compact.json` is the reviewable result. `format-projection.json` records the original 105 MiB replay SHA and all declaration pointers. The projection only replaces repeated calibration declarations with references to the unchanged, executed case files. Full observations, predictions, parameter queries, input identities and numerical results are unchanged. The oversized local original is not added to Git. The builder now references prior calibration evidence by case SHA and JSON pointer for subsequent generation; the already executed cases are preserved exactly.

Validation: `body-independent-review.json` independently checks 693 population/endpoint/error statements; `parameter-independent-review.json` checks 352 source histogram, mean, query-count and prior-rule preservation statements. Both pass. Peak fresh prediction RSS is 195,133,440 bytes; all three predictions completed within the original 90-second per-case budget. No raw capture was scanned to construct these service parameters.

Remaining same-shape ambiguity is explicit: the BF16 `[M,256,2048]` native matrix population has 80 calls per forward, while the declared router has 40. A retained c64 local sequence shows a router before TopK and a separate shared-FFN gate-up before SwiGLU with the same tensor contract. This batch does not apply the pooled 80-call timing twice to the router or assign a fabricated per-role mean. Further source alignment must preserve those distinct roles.

Reproduction uses `build_qwen35_highconc_service.py`, `replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90`, `compact_qwen35_highconc_replay.py`, and `review_qwen35_highconc_service.py`. The manifest and cases pin all inputs. Rebuilding with the revised metadata-pointer producer creates new input hashes and must be recorded as a new replay generation.
