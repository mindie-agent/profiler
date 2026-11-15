# mindie-profiler 0.5.2

[中文](profiler-0.5.2.md)

This release delivers Decode and Prefill structural decomposition, measured event attribution, and the unified offline validation pipeline while preserving all CLI help and error-diagnostics improvements from `0.5.1`:

- **Unified event & native tensor contract parsing**: Normalizes CSV, SQLite DB, and JSON Trace events against `mindie-sim` declared model graphs, fused subgraph boundaries, and physical resource domains across Attention, KV Cache, GDN/KDA, MoE, mHC, residual, and fused operators.
- **Automatic Decode Body & per-layer segmentation**: Identifies complete Decode bodies and layer boundaries directly from retained `kernel_details.csv` captures, reporting union device activity, internal uncovered gaps, outer model stages, and AICPU controller waits separately.
- **Isomorphic cohort reconciliation**: Groups operator cohorts by full tensor contract and physical workload without guessing layer indices under graph replay when layer-level evidence is absent. Calls `> 50 us` use a `15%` relative tolerance; calls `<= 50 us` use a `15 us` absolute tolerance.
- **Single validation pipeline & externalized SHA256 evidence**: Consolidates ad-hoc dated directories and one-off scripts into `examples/structure/pipeline.py`, `cases.json`, and `results/`. Every run re-predicts from a single pinned `mindie-sim` build, stores full per-source reports externally behind SHA256 pointers, and keeps tracked JSON scoreboards under `5 MB`.
- **Frozen train/holdout splits & physical service domains**: Service-domain calibration records explicit train vs. holdout source SHA256 sets, kernel implementations, dtypes, layouts, and execution boundaries. Single-point timings are never copied across TP degrees or concurrency levels, and in-sample calibration scores are never presented as blind holdout generalization.
- **Unified Prefill & Engine boundaries**: Prefill and Engine validation run through the same pipeline entrypoint. Prefill compares Body latency across complete chunks, while client TTFT, device cycles, MTP/outer intervals, and completion-token TPOT retain distinct boundaries. Unmet serving contracts or prediction timeouts fail explicitly rather than producing synthetic passes.

Current offline replay summaries live under `examples/structure/results/`. All hardware evidence comes from offline replay of retained A3/A5 captures with zero live device jobs launched during this release; raw captures and external full reports are excluded from Git tracking and wheels.

All 66 baseline Decode cases pass in this unified replay, while expanded cross-TP and long-context holdouts retain reported failures (operator-domain pass rates do not substitute for whole-Body accuracy). Exporting the full DeepSeek-V4.1 DP8 structure with `mindie-sim 0.8.0` exceeded the `512 MiB` memory budget, and those operator rows explicitly record the resource-gate failure pending bounded indexing in a subsequent release.

Structure attribution and cost reconciliation pair with `mindie-sim 0.8.0` pinned to its formal release commit. Release benchmark attachments record the exact clean source revision, test outcomes, and measured verification metrics, reporting execution status, evidence completeness, and accuracy pass/fail as separate dimensions.
