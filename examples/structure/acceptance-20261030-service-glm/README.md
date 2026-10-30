# GLM A5 observable service replay

Nine explicit source cases use the full native-call mean at the corresponding physical shape domain. These are in-sample calibration results; native ABI admission and source uncertainties remain separate. No Body residual is used to assign parameters.

The common Engine applies each response inclusively at the native boundary. The analytical physical program and dependencies remain; each native HCCL group receives one response, not one per phase.

| Capture | F | Real Mean / P50 / P90 ms | Sim ms | Error | Body result |
|---|---:|---:|---:|---:|---|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233 / 46.498735 / 46.644535 | 43.792001 | -5.88% | PASS |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964 / 37.665316 / 37.761150 | 32.860996 | -12.76% | PASS |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189 / 38.721850 / 38.759233 | 33.213528 | -14.21% | PASS |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918 / 33.026482 / 33.164019 | 27.597449 | -16.45% | FAIL |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091 / 33.625860 / 33.709694 | 27.761141 | -17.42% | FAIL |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324 / 28.828410 / 28.884507 | 23.245099 | -19.38% | FAIL |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246 / 21.408145 / 21.432068 | 16.206457 | -24.33% | FAIL |
| glm53flash-a5-tp8-c3 | 53 | 21.067549 / 21.057180 / 21.170037 | 17.426155 | -17.28% | FAIL |
| glm53flash-a5-tp8-c1 | 65 | 15.683328 / 15.670472 / 15.738329 | 11.715753 | -25.30% | FAIL |

Rules hit exactly 90 AR, 68 copy, 42 routing, 42 fused GMM, 34 convolution and 34 KDA calls per Forward in all 9 cases. Other observed geometries remain deferred by `--geometry-limit 1`; they are not included in the selected Forward denominator.

AR uses typed COMMUNICATION envelopes, not AI_CPU controllers. Payload and Mesh OneShot are declared source conditions; elapsed service can include peer wait and is not a pure link-rate observation. Copy service uses a pooled gather/scatter mean assigned symmetrically; direction-specific timing is not claimed. Routing valid group-list values, source binary identity and full native ABI gaps are not filled by calibration.

Reproduce from the fixed `2f48346b` checkout with its package on `PYTHONPATH`:

```sh
python build_service_cases.py
python ../replay_decode_forwards.py --manifest decode-forward-service-cases.json --output decode-forward-service-replay.json --geometry-limit 1 --prediction-timeout 90 --runtime-source-commit 2f48346b
python review_service_replay.py
```

Saved-population/identity/hit review: 625 checks, 0 failures. The initial reviewer-only size-field assumption was corrected; it did not represent a capture or prediction failure. Cost execution and memory receipts are retained in `decode-forward-service-replay.json`. No CSV parsing or device collection was performed; the shared replay adapter revalidates source hashes.

Standard independent Body arithmetic/population review: 1,821 checks / 0 failures. `remaining-native-activity.md` lists the six unsuccessful cases’ measured native families outside these service rules; it does not claim they are absent from the analytical model.
