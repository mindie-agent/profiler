# GLM layer-ordered AI_CPU metadata response

The explicit source caller creates 11 singleton MLA metadata groups. Each follows its layer index selection and feeds a separate 1024-word publication before the layer attention. The metadata build alone receives that source’s complete native-call Mean; neither publication nor attention receives a duplicate parameter. No before-forward hoisting is selected.

All nine sources retain their previous responses. Parameters are observed and in-sample. Six retained low-source integer-ns examples show MLA layers 3/7 after index-score and before SparseFlashMla on the same stream; they do not identify every capture dependency, binary, or complete native ABI. Thus singleton caller placement is an explicit source condition, not a new strict tensor binding. Native activity is not assumed additive to Body time.

| Source | F | Real Mean/P50/P90 ms | Previous Sim ms | New Sim ms | Error | Body | Metadata Mean/P50 us |
|---|---:|---:|---:|---:|---:|---|---:|
| a5_glm53flash_tp8_c64_p4k | 31 | 46.528233/46.498735/46.644535 | 47.071528 | 47.971347 | +3.10% | PASS | 81.799663/78.398000 |
| a5_glm53flash_tp8_c32_p4k | 31 | 37.668964/37.665316/37.761150 | 35.167461 | 35.809299 | -4.94% | PASS | 58.346909/54.620000 |
| a5_glm53flash_tp8_c32_p8k | 35 | 38.713189/38.721850/38.759233 | 36.207062 | 36.851628 | -4.81% | PASS | 58.594875/55.515000 |
| a5_glm53flash_tp8_c16_p4k | 30 | 33.030918/33.026482/33.164019 | 29.627802 | 30.186894 | -8.61% | PASS | 50.824539/47.814000 |
| a5_glm53flash_tp8_c16_p8k | 32 | 33.616091/33.625860/33.709694 | 30.209746 | 30.768298 | -8.47% | PASS | 50.775406/47.836500 |
| a5_glm53flash_tp8_c8_p4k | 30 | 28.833324/28.828410/28.884507 | 25.431005 | 25.914815 | -10.12% | PASS | 43.980688/41.179500 |
| a5_glm53flash_tp8_c4_p8k | 11 | 21.418246/21.408145/21.432068 | 18.190524 | 18.622768 | -13.05% | PASS | 39.292826/36.752000 |
| glm53flash-a5-tp8-c3 | 53 | 21.067549/21.057180/21.170037 | 18.251869 | 18.663071 | -11.41% | PASS | 37.379957/34.307000 |
| glm53flash-a5-tp8-c1 | 65 | 15.683328/15.670472/15.738329 | 13.267585 | 13.652393 | -12.95% | PASS | 34.980463/31.811000 |

9/9 Body PASS; 1586 population/dependency/application checks and 0 failures. The standard independent Body review is separate. No raw read or device collection. Runtime changed from 672a to 13862d5e; the numerical delta is not an isolated additive metadata estimate.

Reproduce: ../inspect_metadata_placement.py, ../build_metadata_pass.py with fixed 13862d5e on PYTHONPATH; replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90; ../review_metadata_pass.py and review_decode_predictions.py.
