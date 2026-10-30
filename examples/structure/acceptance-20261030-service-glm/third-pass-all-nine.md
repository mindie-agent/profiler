# GLM uniform HC source domain: all nine captures

All eligible captures use the same eleven-mechanism source configuration. Responses remain each capture’s observed native Mean. The three earlier executions were retained; only the other six were newly run. No selection depends on whether a previous result passed.

| Source | F | Real Mean ms | Previous Sim ms | Current Sim ms | Current error | Previous → current |
|---|---:|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233 | 43.792001 | 44.975945 | -3.336% | PASS → PASS |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964 | 32.860996 | 33.490957 | -11.091% | PASS → PASS |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189 | 33.213528 | 34.534175 | -10.795% | PASS → PASS |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918 | 28.190842 | 27.798268 | -15.842% | PASS → FAIL |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091 | 28.780617 | 28.388297 | -15.551% | PASS → FAIL |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324 | 23.920949 | 23.473335 | -18.590% | FAIL → FAIL |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246 | 17.042668 | 16.381328 | -23.517% | FAIL → FAIL |
| glm53flash-a5-tp8-c3 | 53 | 21.067549 | 18.000395 | 16.914170 | -19.715% | PASS → FAIL |
| glm53flash-a5-tp8-c1 | 65 | 15.683328 | 12.503766 | 11.953329 | -23.783% | FAIL → FAIL |

Uniform current result: 3/9 PASS, previously 6/9. Selected population: 318 Forward; all retained geometries: 34 / 368 Forward. Deferred geometries are not added to the scored population.

All 99 rule/source combinations hit. MoeInitRoutingV3 (42/F) and pooled convolution-state copy (68/F) were already represented and are not charged twice. The normalized HC contract supports the premix-absent branch; the provider removes six standalone phases and adds one whole-native boundary per HC call. No obsolete decomposition is restored to recover a pass.

Remaining Slice (mixed 224/F) and sparse-attention metadata (11/F) require independent physical role boundaries. Their unscored elapsed time is not a zero-cost assumption or an additive Body deficit.

Nine total fresh predictions across the two retained reports; 126.575s, maximum RSS 127.06MiB. No new raw parsing or device collection. Runtime: 3b72ea2d. In-sample service calibration; strict ABI coverage stays separate.
