# Qwen3.5-397B A3 TP16 native GQA/GMM and HCOM curve

This arm reuses the existing c48/c136 captures and their accepted Body windows. Execution shapes are q4/B64/M256 and q4/B160/M640, independently of client concurrency labels. A single retained-window stream per source saved 107/114 complete native ABI partitions for 23/18 forwards. The two scans retained 99,979 positive events from 120,639 parsed CSV rows, took 5.909 seconds and peaked at 62,160,896 bytes. No remote collection was performed.

Each source has complete populations of 60 fused `GroupedMatmulSwigluQuant`, 60 down `GroupedMatmul`, 15 `FusedInferAttentionScore`, and 120 typed HCOM AllReduce envelopes per forward. INT8 up/activation/output quantization is lowered to one existing native fusion boundary; its full observed service is applied once, not once per internal phase. Down and GQA are independently bound to their physical geometry. Native group-list values remain unobserved: M2560/6400 buffer rows agree with the declared top-10 aggregate, but do not establish per-expert valid counts or the captured expert distribution.

The local TP16 payload is independently declared as 2,097,152/5,242,880 bytes. `AICPU_TS/mesh_twoshot` is an explicit source condition, not an observed algorithm. The complete 120-call envelope population is pooled once across the source-declared TP boundaries; AICPU controller events are excluded and the histogram is independently identical to the retained typed HCCL ledger. Its measured elapsed includes protocol/peer waiting and is not link bandwidth. Joint native service replaces the local GMM/GQA analytic schedule with a busy-ns response while preserving analytic reference work; HCOM uses the existing whole-collective completion response.

| Case | Real ms | Sim ms | Error | ≤15% | ≤8% |
|---|---:|---:|---:|---|---|
| c48 | 76.089008 | 67.050948 | −11.8783% | pass | fail |
| c136 | 119.054350 | 113.556975 | −4.6175% | pass | pass |

All four rules per source hit their exact 60/60/15/120 populations. The c48 result worsens from its earlier baseline and is retained honestly. Runtime is Sim `21c30821d87a757bace8cf6b2fffea2536db643e`; maximum prediction RSS was 124,993,536 bytes, with 5.331/5.530 seconds per source. Calibration is explicitly in-sample, with source conditions retained. No Body residual or target threshold was used to assign a parameter.

`decode-forward-cases.json`, `observed-populations.json`, native partitions and the complete replay are retained. Standard Body review has 500 checks and zero failures; parameter/native/HCOM review has 195 checks and zero failures. Reproduce with `collect_qwen397_retained_native.py`, `build_qwen397_highconc_service.py`, and the ordinary `replay_decode_forwards.py` CLI using the saved manifest.
