# Retained Decode FIA and Hc PMU Evidence

Full original CSV scans, using the shared profiler decoder. Query widths select descriptors; they do not prove phase, context, step, layer or native dispatch.

Block Num and Mix Block Num remain observed launch fields. They are not a measurement of `kv_splits`. PMU time fields are converted from us to ns once; cycles, ratios and percent retain their exported units. PMU intervals may overlap and must not be added as elapsed kernel time.

| Capture / type / query rows | Events | Tensor descriptors / state groups |
| --- | ---: | ---: |
| a3_qwen35 / FusedInferAttentionScore / 1 | 0 | 0 / 0 |
| a3_qwen35 / FusedInferAttentionScore / 2 | 715 | 1 / 1 |
| a3_qwen36 / FusedInferAttentionScore / 1 | 34 | 1 / 1 |
| a3_qwen36 / FusedInferAttentionScore / 4 | 255 | 1 / 2 |
| a3_v4pro / HcPre / None | 496 | 1 / 1 |
| a3_v4pro / HcPost / None | 496 | 1 / 1 |

| Capture / descriptor / state | Events | Block/Mix counts | Duration mean / min / max (us) |
| --- | ---: | --- | --- |
| a3_qwen35 / FusedInferAttentionScore / 183265638704 / static | 715 | 17/34:715 | 53.573506 / 47.641000 / 61.721000 |
| a3_qwen36 / FusedInferAttentionScore / f8d2fa2eef7b / dynamic | 34 | 17/34:34 | 54.717000 / 46.599000 / 63.698000 |
| a3_qwen36 / FusedInferAttentionScore / 20e8928bb2b1 / dynamic | 15 | 17/34:15 | 58.485533 / 52.779000 / 64.259000 |
| a3_qwen36 / FusedInferAttentionScore / b8af2605c95f / static | 240 | 17/34:240 | 58.173563 / 53.779000 / 64.159000 |
| a3_v4pro / HcPost / 7507f0864ecf / dynamic | 496 | 40/0:496 | 202.098462 / 197.856000 / 210.536000 |
| a3_v4pro / HcPre / 9009c2e9f897 / dynamic | 496 | 20/40:496 | 191.803266 / 177.276000 / 207.216000 |

| Descriptor | AIC total / MAC / MTE1 / MTE2 / scalar mean (us) | AIV total / vector / MTE2 / MTE3 / scalar mean (us) |
| --- | --- | --- |
| 183265638704 | 41.034593 / 2.032204 / 5.519343 / 19.958474 / 24.729301 | 44.791843 / 1.102203 / 3.991267 / 1.202494 / 19.137119 |
| f8d2fa2eef7b | 42.407441 / 1.956529 / 5.349500 / 21.509412 / 26.096735 | 45.857971 / 0.982647 / 5.126559 / 1.415441 / 18.240353 |
| 20e8928bb2b1 | 42.174000 / 3.439067 / 5.900267 / 21.801133 / 28.209333 | 47.791600 / 1.939667 / 4.857733 / 3.010400 / 17.999067 |
| b8af2605c95f | 41.184725 / 3.450229 / 5.864596 / 22.164279 / 25.930037 | 47.606817 / 1.937246 / 5.232392 / 3.413446 / 16.390650 |
| 7507f0864ecf | 0.000000 / 0.000000 / 0.000000 / 0.000000 / 0.000000 | 195.358974 / 165.027540 / 66.436433 / 19.572288 / 56.152667 |
| 9009c2e9f897 | 121.639099 / 48.174593 / 62.600153 / 65.758996 / 43.630966 | 183.594526 / 60.129593 / 68.791480 / 55.076990 / 71.008325 |

The JSON preserves every selected descriptor's six original tensor fields, all exported PMU distributions, missing/zero counts and source line samples. Tensor descriptor identity excludes core and OP State; execution groups retain those fields so dynamic/static exports are not silently conflated. Histograms use eight logarithmic bins per power of two; extrema and arithmetic means are streamed exactly up to floating-point arithmetic. No per-event values are retained, no simulation is executed, and no new NPU capture is collected.
