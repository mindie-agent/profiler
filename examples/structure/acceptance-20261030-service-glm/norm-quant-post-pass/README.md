# GLM complete normalization, quantization and HCPost service

All nine sources retain their prior matrix/Slice and eleven original responses. The same seven additions apply throughout: attention and FFN RMSNorm (45+45 calls/F), quantization at three physical shapes (45+3+42), and attention/FFN native HCPost (45+45). HCPost uses the existing arch35 BF16 whole-call provider; the former 90 semantic nodes are replaced once.

Dense and shared gate-up quantization share one exact physical shape/contract. Their complete 3+42 call populations are pooled by event count into one explicit joint response; this is not an independently identified per-role latency. Other blocks/shapes remain separate. All parameters are observed, in-sample and derived from full histograms, never Body error.

| Source | F | Real Mean / P50 / P90 ms | Previous Sim ms | New Sim ms | Error | Body | Rules |
|---|---:|---:|---:|---:|---:|---|---:|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233 / 46.498735 / 46.644535 | 45.579052 | 47.071528 | +1.17% | PASS | 27 |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964 / 37.665316 / 37.761150 | 34.069526 | 35.167461 | -6.64% | PASS | 27 |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189 / 38.721850 / 38.759233 | 35.111231 | 36.207062 | -6.47% | PASS | 27 |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918 / 33.026482 / 33.164019 | 28.455782 | 29.627802 | -10.30% | PASS | 27 |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091 / 33.625860 / 33.709694 | 29.040987 | 30.209746 | -10.13% | PASS | 27 |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324 / 28.828410 / 28.884507 | 24.434071 | 25.431005 | -11.80% | PASS | 29 |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246 / 21.408145 / 21.432068 | 17.394484 | 18.190524 | -15.07% | FAIL | 29 |
| glm53flash-a5-tp8-c3 | 53 | 21.067549 / 21.057180 / 21.170037 | 17.470946 | 18.251869 | -13.37% | PASS | 27 |
| glm53flash-a5-tp8-c1 | 65 | 15.683328 / 15.670472 / 15.738329 | 12.665580 | 13.267585 | -15.40% | FAIL | 29 |

7/9 Body PASS; 1596 retained-population/application checks, 0 failures. All nine were reevaluated regardless of earlier result. No raw scan or device work.

Remaining metadata, unidentified native matrix/elementwise and unpartitioned Slice populations are not assigned synthetic prices. Native activity sums and scheduled intervals are not additive Body causal budgets. Body PASS does not mean all native ABI contracts are closed.

Reproduce with fixed 672a595f: ../build_norm_quant_post_pass.py, replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90, ../review_norm_quant_post_pass.py and review_decode_predictions.py.
