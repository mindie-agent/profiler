# GLM HC atomic source arm

The existing arch35 HCPre provider replaces 540 standalone semantic phases with 90 native occurrences per Forward. The complete retained normalized contract covers the premix-absent branch; it does not establish capture binary identity or optional output storage aliases. Each atomic call receives its observed whole-call Mean once. The 34 QKV projection calls receive their independently observed Mean. Previous nine parameters remain unchanged.

| Source | F | Real Mean / P50 / P90 ms | Previous Sim ms | Current Sim ms | Error | Body result |
|---|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233 / 46.498735 / 46.644535 | 43.792001 | 44.975945 | -3.34% | PASS |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964 / 37.665316 / 37.761150 | 32.860996 | 33.490957 | -11.09% | PASS |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189 / 38.721850 / 38.759233 | 33.213528 | 34.534175 | -10.79% | PASS |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918 / 33.026482 / 33.164019 | 28.190842 | 27.798268 | -15.84% | FAIL |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091 / 33.625860 / 33.709694 | 28.780617 | 28.388297 | -15.55% | FAIL |
| glm53flash-a5-tp8-c3 | 53 | 21.067549 / 21.057180 / 21.170037 | 18.000395 | 16.914170 | -19.71% | FAIL |

3/6 sources pass the 15% Body tolerance. The source configuration applies to every eligible capture irrespective of its prior result. The old decomposition is not restored to improve error. The prior runtime was 2f48346b and this runtime is 3b72ea2d, so the difference is not attributed solely to HC.

All eleven regimes hit exactly their declared native multiplicities. These are explicit in-sample measured service parameters, not a held-out validation and not a claim that every native ABI is closed. Scheduled family intervals include contention and are not additive Body budgets.

Slice (224 calls/F) and SparseFlashMlaMetadata (11 calls/F) remain separate unresolved physical-boundary work. No observed time is attached to an unproven view/copy/metadata mapping.

Retained-population/rule review: 690 checks, 0 failures. Body arithmetic and unchanged source/geometry checks are in body-independent-review.json. 6 fresh predictions, no raw parsing or device collection; the shared replay validates source file identities.

Reproduce with fixed 3b72ea2d on PYTHONPATH. The initial three inputs use ../build_third_pass.py; the remaining six use ../build_remaining_six.py. Replay this manifest through ../../replay_decode_forwards.py with --geometry-limit 1 --prediction-timeout 90, then run ../review_third_pass.py with this directory as the positional argument.
