# Q397 complete matrix and GDN domains: correction exposes remaining error

This follow-up preserves the first arm's four GQA/GMM/TP16 rules and the same 23/18 accepted forwards. It adds eight complete native domains per source: 375 BF16 `MatMulV2` calls and 45 `RecurrentGatedDeltaRule` calls per forward. Each native ABI is projected through the shared contract parser and must identify one physical operator in every retained layer. All matching roles are included, regardless of whether correcting their service improves Body error.

The independent `shared_expert` category is corrected to BF16, as observed in all retained descriptors. This removes 120 inappropriate shared-FFN quantizers. GQA output projection remains excluded: its 15 BF16 native calls conflict with the current INT8 `attn` source category shared with the genuinely INT8 QKV projection. Changing the whole attention category would introduce another incorrect declaration. This gap is not assigned a service value.

The eight additional rules use the joint-native busy-ns resource once per native kernel. All 420 expected calls are hit, with each source's complete integer histogram mean. Prior four rules are unchanged. No Body residual or target threshold enters any parameter.

| Case | Real ms | Corrected Sim ms | Error | ≤15% | ≤8% |
|---|---:|---:|---:|---|---|
| c48 | 76.089008 | 61.284580 | −19.4567% | fail | fail |
| c136 | 119.054350 | 104.481729 | −12.2403% | pass | fail |

The earlier c136 −4.62% does not survive this additional source correction. Its more accurate local services reduce prior analytic overestimation, exposing other gaps. The result is retained rather than selecting the previous arm for a better score. Remaining observed unparameterized domains include `MoeInitRoutingV3` and a separate `Cumsum`; the former has an INT8 quantized output while the old source route-pack and quantization are split, so an inclusive response must not be attached twice. Controller-only AICPU elapsed remains outside physical service assignments.

Runtime: `21c30821d87a757bace8cf6b2fffea2536db643e`. No new raw pass was needed. `parameter-independent-review.json` checks 311 statements and the standard Body review checks 500, both with zero failures. The actual comparison remains 1/2 passed at 15%, 0/2 at 8%. All calibration is explicitly in-sample, and unknown expert-distribution/transport conditions are retained from the prior arm.
