# GLM second observed-service arm

This separate arm adds complete-population service means for expert-down GroupedMatmul, whole-batch SparseFlashMla and the standalone index-score kernel. The original six rules and physical program selections are byte-for-byte unchanged. All results are in-sample; no Body residual determines the three new parameters.

| Case | F | Real Mean / P50 / P90 ms | First Sim ms | Second Sim ms | Error | Body result |
|---|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918 / 33.026482 / 33.164019 | 27.597449 | 28.190842 | -14.65% | PASS |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091 / 33.625860 / 33.709694 | 27.761141 | 28.780617 | -14.38% | PASS |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324 / 28.828410 / 28.884507 | 23.245099 | 23.920949 | -17.04% | FAIL |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246 / 21.408145 / 21.432068 | 16.206457 | 17.042668 | -20.43% | FAIL |
| glm53flash-a5-tp8-c3 | 53 | 21.067549 / 21.057180 / 21.170037 | 17.426155 | 18.000395 | -14.56% | PASS |
| glm53flash-a5-tp8-c1 | 65 | 15.683328 / 15.670472 / 15.738329 | 11.715753 | 12.503766 | -20.27% | FAIL |

The added native boundaries receive 42, 11 and 11 responses per Forward. Index-score HBM-work coordinates distinguish context lengths even when the displayed input shape is equal; index_topk and projections remain separate. B=1 indexed attention uses its existing single-sequence source boundary, while B>1 uses the declared complete-batch boundary. No sequence subset is substituted for a full native call.

Forced-balanced grouped work, sparse-index/active-context values and captured binary identity remain source conditions. Service calibration changes no strict ABI admission. Each response remains an inclusive lower bound on completion under the preserved physical schedule, not extra delay summed over phases.

Saved-native/first-arm/hit verification: 279 checks / 0 failures. Independent Body arithmetic review is recorded in body-independent-review.json. No capture was parsed or newly collected.

The initial six executions are retained in initial-selector-attempt-replay.json. Four small-M sources missed the GMM rule because matrix_groups was incorrectly equated with the 288 stored weight banks. The corrected physical selector uses the actual active group count plus a separate weight-bank guard. All six revised inputs were freshly predicted (12 total second-arm executions across two attempts); response means never changed. selector-correction.json preserves each exact earlier rule and case hash, independently reconstructible from the final inputs.

Reproduce with the fixed 2f48346b runtime on PYTHONPATH: run ../build_second_pass.py; replay this manifest through ../../replay_decode_forwards.py with --geometry-limit 1 --prediction-timeout 90; then run ../review_second_pass.py.
