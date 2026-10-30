# Qwen3.5 TP4 complete observed service responses

The final three primary Decode populations pass the unchanged 15% Body criterion on Sim `672a595fb1e102208d9fc904fad0ec9180fa437a`. This is **in-sample observable-service calibration**, not a claim of held-out accuracy. No Body error or target threshold enters a response parameter. Original Body spans, all 286 accepted forwards and all 40 geometry populations remain unchanged; the three main populations contain 239 forwards. Other geometries remain deferred.

| Source | Main forwards | Real mean ms | Sim ms | Relative error | Final receipt |
|---|---:|---:|---:|---:|---|
| c4, q4/B4 | 84 | 11.551366762 | 9.857738201 | −14.6617% | `decode-forward-c4-gdn-helpers-replay.json` |
| c64, q4/B64 | 79 | 21.956844696 | 18.821945853 | −14.2775% | `decode-forward-complete-service-replay.json` |
| c128, q4/B128 | 76 | 28.584773553 | 24.707429948 | −13.5644% | `decode-forward-complete-service-replay.json` |

`decode-forward-final-cases.json` joins the final three declarations for future replay. It does not claim a new combined execution. For scoreboard integration, append the complete-service receipt first, then the final c4 GDN-helper receipt. Existing source IDs are unchanged. Runtime package fingerprint is `c347250c5f5e8aeccd0abda9d2a96a8e22928e2ed8668aed825671276f0e2ce5` (283 files).

The first pass adds exact, complete MatMulV3 and RecurrentGatedDeltaRule cohort means to all three cases, and a c4-only DSQ response. The old two MXA8W4/NZNK rules have no matching Q35 workload and are removed. Seven applicable prior rules retain their exact parameters. One same-shape MatMul population has 80 measured calls per Forward but only 40 fresh router candidates; it is explicitly excluded from parameter assignment. Its total timing is never assigned to 40 router calls.

The c4 extension adds six other complete contracted populations (Conv, two Slice boundaries, SwiGlu, QKV matrix and cache) and replaces two bank-scaled GMM responses with the corresponding complete native-call means. This does not stack two service floors. New retained GMM data separately establishes INT32 up output, DSQ INT8 output plus FP32 row scale, and the downstream consumer slots. Allocation capacity 128 is distinct from declared active rows 32; actual group-list values and tensor-address aliasing remain unobserved.

The final c4 responses preserve weaker evidence explicitly:

- FIA has a complete GQA-topology timing population of 840 calls, matching ten declared whole-batch programs per Forward. Two normalized contract examples agree with q4/B4, four query heads and width 256. They are not represented as full-population native ABI evidence. Context 4096 is a source declaration, not inferred from KV capacity. Exactly ten response hits are verified.
- GDN gating, Q/K L2 normalization and gated output normalization have complete GDN-attention populations of 30/60/30 calls per Forward. Source semantic boundaries identify four physical recipe domains, each hit 30 times. The two Q/K domains share their complete pooled native mean; separate Q and K measured timings are not invented. Compiled binary identity and full native descriptors remain unproven.

These are valid explicitly scoped observable-service parameters. Their use does not change cohort strict admission, invent ABI evidence, or turn service activity into additive Body wall time. All response values are means of original integer duration histograms. Existing source programs, dependencies, physical work and contention remain active.

Four actual execution receipts preserve progression, including failures:

| Execution | Compared | Passed | c4 error | Elapsed s | Max worker MiB |
|---|---:|---:|---:|---:|---:|
| Complete contract populations | 3 | 2 | −21.3876% | 54.313 | 173.53 |
| c4 complete local/GMM extension | 1 | 0 | −16.7601% | 6.125 | 127.50 |
| c4 whole-batch FIA response | 1 | 0 | −15.6367% | 6.280 | 128.02 |
| c4 source GDN-helper responses | 1 | 1 | −14.6617% | 5.965 | 131.19 |

All six worker executions were new on this runtime. There were no raw CSV scans, no new device work and no changes to Sim, profiler core or historical receipts. Seven real-population regressions pass; four independent Body arithmetic reviews total 1,239 checks with zero failures. The builder was extended between the independent c4 arms; each execution retains its original case and worker identities. The initial population artifact records the initial builder generation, while the committed builder contains all four reproducible generation paths.

Reproduce metadata with `build_qwen35_complete_service_cases.py`, followed by `--extend-c4`, `--extend-c4-attention`, and `--extend-c4-gdn-helpers` after the preceding receipt exists. Use `replay_decode_forwards.py --geometry-limit 1 --reuse-extractions ../acceptance-20261030-qwen35-observed-service --runtime-source-commit 672a595fb1e102208d9fc904fad0ec9180fa437a`; preserve each output path so the failed intermediate arms remain visible.
