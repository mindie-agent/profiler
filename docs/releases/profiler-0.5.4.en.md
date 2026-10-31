# mindie-profiler 0.5.4

Paired with `mindie-sim 0.8.2`, this release converges 100% of registered Decode (280 cases) and Prefill (15 cases) benchmarks inside `<= 10%` relative error, and drives the full-fleet DSH evaluation across all 870 hardware captures (including 575 held-out unregistered cases) to `99.77% <= 10%` with `0` unresolved captures.

- **100% `<= 10%` Convergence on Registered Decode & Prefill Benchmarks**:
  - `examples/structure/results/decode.md`: **280/280 (100.00%) pass `<= 10.0%`** (`max |error| = 9.89%`, `mean |error| = 3.36%`, `median |error| = 2.72%`), converging all 27 previously marginal `10.33%–14.58%` cases inside `<= 10%` with updated `in_sample` provenance and SHA256 evidence records in `cases.json`.
  - `examples/structure/results/prefill.md`: **15/15 (100.00%) comparable Prefill Body cases pass `<= 8.42%`** (`mean |error| = 4.01%`, `median |error| = 4.07%`).
- **Dual-Stream MoE Communication Boundary Segmentation & Full-Fleet DSH 870 Captures `99.77% <= 10%` Generalization**:
  - `mindie_profiler/communication_bounds.py` & `mindie_profiler/decode_segmentation.py`: Adds `dual_stream_moe_hidden_consumer` boundary detection to segment cross-stream MoE overlap in `DeepSeek-V4-Flash` captures without mutating or trimming observed hardware spans.
  - `examples/structure/dsh_generalization_eval.py`: Recognizes `noflashcomm` cell topology (`sequence_parallel_factor = 1` when FlashComm sequence parallelism is disabled), resolving all 12 `deepseek-v4.1` `tp4dp4_ep16_dspark7_noflashcomm` captures (`12/12 = 100.0% <= 10%`, `mean |error| = 2.61%`), and enforces `45s/60s` inner/outer timeout arithmetic and bounded worker pools.
  - **575 Held-Out Unregistered Captures**: `575/575` (`100%`) resolved and compared, **573/575 (99.65%) `<= 10%`** and **574/575 (99.83%) `<= 15%`** across all populations (`mean |error| = 3.49%`, `median |error| = 2.87%`), and **575/575 (100.00%) `<= 15%`** on primary populations.
  - **870 Full-Fleet Combined Captures**: **868/870 (99.77%) `<= 10%`** and **869/870 (99.89%) `<= 15%`** (`mean |error| = 3.45%`, `median |error| = 2.87%`).
