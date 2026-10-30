# GLM HC atomic source arm

The existing arch35 HCPre provider replaces 540 standalone semantic phases with 90 native occurrences per Forward. The complete retained normalized contract covers the premix-absent branch; it does not establish capture binary identity or optional output storage aliases. Each atomic call receives its observed whole-call Mean once. The 34 QKV projection calls receive their independently observed Mean. Previous nine parameters remain unchanged.

| Source | F | Real Mean / P50 / P90 ms | Previous Sim ms | Current Sim ms | Error | Body result |
|---|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324 / 28.828410 / 28.884507 | 23.920949 | 23.473335 | -18.59% | FAIL |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246 / 21.408145 / 21.432068 | 17.042668 | 16.381328 | -23.52% | FAIL |
| glm53flash-a5-tp8-c1 | 65 | 15.683328 / 15.670472 / 15.738329 | 12.503766 | 11.953329 | -23.78% | FAIL |

All three remain outside the 15% Body tolerance. Source-consistent fusion reduces prediction rather than adding arbitrary delay; the old decomposition is not restored to improve error. The prior runtime was 2f48346b and this runtime is 3b72ea2d, so the difference is not attributed solely to HC.

All eleven regimes hit exactly their declared native multiplicities. These are explicit in-sample measured service parameters, not a held-out validation and not a claim that every native ABI is closed. Scheduled family intervals include contention and are not additive Body budgets.

Slice (224 calls/F) and SparseFlashMlaMetadata (11 calls/F) remain separate unresolved physical-boundary work. No observed time is attached to an unproven view/copy/metadata mapping.

Retained-population/rule review: 228 checks, 0 failures. Body arithmetic and unchanged source/geometry checks are in body-independent-review.json. Three fresh predictions, no raw parsing or device collection; the shared replay validates source file identities.

Reproduce: run ../build_third_pass.py with fixed 3b72ea2d on PYTHONPATH, then replay decode-forward-service-cases.json via ../../replay_decode_forwards.py with --geometry-limit 1 --prediction-timeout 90, and run ../review_third_pass.py.
