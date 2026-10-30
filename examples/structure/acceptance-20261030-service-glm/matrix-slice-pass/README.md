# GLM complete matrix and packed KDA copy service

Nine previously unified HC sources are all evaluated. Each adds nine complete matrix cohorts (199 calls/Forward) with shape-specific native Mean, while keeping the prior eleven responses unchanged. Two common tensor materializations are enabled for all nine: convolution input and KDA beta, each 34 calls/Forward. Only the three sources with full retained Slice ABI/histograms receive their own observed copy responses; the other six retain physical copy cost without borrowed parameters.

| Source | F | Real Mean/P50/P90 ms | Previous Sim ms | New Sim ms | Error | Body | Rules | Observed new Slice calls/F |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233/46.498735/46.644535 | 44.975945 | 45.579052 | -2.04% | PASS | 20 | 0 |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964/37.665316/37.761150 | 33.490957 | 34.069526 | -9.56% | PASS | 20 | 0 |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189/38.721850/38.759233 | 34.534175 | 35.111231 | -9.30% | PASS | 20 | 0 |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918/33.026482/33.164019 | 27.798268 | 28.455782 | -13.85% | PASS | 20 | 0 |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091/33.625860/33.709694 | 28.388297 | 29.040987 | -13.61% | PASS | 20 | 0 |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324/28.828410/28.884507 | 23.473335 | 24.434071 | -15.26% | FAIL | 22 | 68 |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246/21.408145/21.432068 | 16.381328 | 17.394484 | -18.79% | FAIL | 22 | 68 |
| glm53flash-a5-tp8-c3 | 53 | 21.067549/21.057180/21.170037 | 16.914170 | 17.470946 | -17.07% | FAIL | 20 | 0 |
| glm53flash-a5-tp8-c1 | 65 | 15.683328/15.670472/15.738329 | 11.953329 | 12.665580 | -19.24% | FAIL | 22 | 68 |

5/9 Body PASS. 1475 retained-population and application-count checks, 0 failures. The runtime changed to 672a595f, so the Body delta is not an isolated matrix/copy causal allocation.

All parameters are explicitly observed and in-sample. Matrix geometry normalization does not establish captured tiling or Host occurrence. Slice start-offset scalars are not exported; source-packed layout and actual output geometry support the conditional correspondence. NCL beta input remains in provenance. No whole mixed Slice population, Body residual, metadata CPU latency, or already-covered copy/routing response is used to fill a gap.

SparseFlashMlaMetadata remains a typed AI_CPU dependency requiring its own source node. Unresolved MatMul/quant matrix subpopulations remain unchanged. No new raw scan, device call, or measured parameter extrapolation.

Reproduce: run ../build_matrix_slice_pass.py with fixed 672a595f on PYTHONPATH, replay decode-forward-service-cases.json with replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90, then run ../review_matrix_slice_pass.py and review_decode_predictions.py.
