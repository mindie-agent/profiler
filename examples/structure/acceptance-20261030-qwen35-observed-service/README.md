# Qwen3.5 TP4 / EP4 observed-service replay

The [input preflight](input-preflight.json) reuses three controller-corrected captures and the previously retained full native ABI partitions. The main q4 populations are c4/B4/M16: 84 forwards; c64/B64/M256: 79; c128/B128/M512: 76. All 286 complete forwards remain in the original extractions; the three main groups total 239.

`prepare_manifest.py` verifies source identity, complete native duration-histogram counts, q/B/M, and identical first-norm/LMHead occurrences across the historical native partition and the corrected controller boundary generation. It does not rescan CSV, predict cost, fit parameters, or rewrite Sim cases.

The source-authored grouped/DSQ/MC2/HCCL cases were committed in Sim `3a98c2df` and independently replayed on fixed `84d80b40dca5a462ff32b971152c2f2e81abfc4b`. The exact case bytes and observed populations are pinned by `case-overrides.json`, `decode-forward-service-cases.json` and `input-preflight.json`. No parameter was fitted here.

| Source | Main forwards | Real Mean ms | Sim ms | Error | Body pass | Layer pass |
|---|---:|---:|---:|---:|---|---:|
| c4 | 84 | 11.551367 | 8.453750 | −26.8160% | No | 0/40 |
| c64 | 79 | 21.956845 | 18.692892 | −14.8653% | Yes | 29/40 |
| c128 | 76 | 28.584774 | 24.288207 | −15.03096% | No | 29/40 |

The unrounded 15% threshold is used. c128 remains a failure. Three fresh workers completed in 5.38/18.90/28.39 seconds, at most 125,648,896 bytes RSS. All 40 observed geometry groups remain in the report; the other 37 are deferred rather than scored as zero. The independent Body arithmetic review passed 693 checks.

Each whole native response is inclusive once. c64/c128 select AllReduce 80 times and AllGather, dispatch, combine, grouped up, grouped down and DSQ 40 times each. c4 selects the same six other rules, while DSQ is outside the explicit large-row domain (rows at least 512 and expert rows at least 8). The two unrelated MXA8W4 rules in the parent configuration do not match these INT8 cases. No silent extension was made to force a rule hit.

All three complete arms mix parameter-assignment and previously observed validation roles. Grouped/DSQ assignment uses c64; the HCCL coefficients use c4 and c128, with c64 excluded only from those HCCL coefficients. Thus no entire arm is a blind holdout. Per-rule provenance remains authoritative. The initial manifest wrongly generalized c128's grouped validation role to the entire arm; the final report records this metadata-only correction and prior SHA, with zero new cost executions and unchanged numbers.

Fresh existing-population operator bills are saved in `native-references/` (33 groups) and `hccl-references/` (27 groups). They preserve all previously referenced histograms, original layers and source identities. The service/operator audit passed 680 checks. These are source-program references; routed buffer capacity is not captured valid rows, and TopK's third FP32 output remains outside its partial work boundary. The prior strict TensorMove supplement still owns its exact FFN partitions; no new reference duplicates those calls. Attention TensorMove gaps remain unresolved. Summed activity residuals are not additive Body latency and do not change strict accuracy denominators.

Once the source cases are committed and the fixed runtime is announced:

```sh
python examples/structure/acceptance-20261030-qwen35-observed-service/prepare_manifest.py \
  --case-overrides examples/structure/acceptance-20261030-qwen35-observed-service/case-overrides.json \
  --runtime-commit 84d80b40dca5a462ff32b971152c2f2e81abfc4b
```

An override maps each unchanged source case ID to `path`, `sha256`, and optional explicitly declared `calibration_evidence`. The resulting manifest is `decode-forward-service-cases.json`; replay uses the existing `replay_decode_forwards.py --geometry-limit 1` without raw parsing.

The first preparation attempt rejected the valid flat `runtime.tp/ep` JSON because it expected a nested `parallel` object. The preparation tool now delegates placement parsing to Sim's existing `parse_case`. No prediction ran from that rejected input. Replaying requires the pinned source version; it does not silently substitute the latest runtime.
