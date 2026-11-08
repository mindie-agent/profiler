# mindie-profiler 0.5.7

[中文](profiler-0.5.7.md)

## Four-Level Piecewise Zero-Shot Validation (L1–L4) & A5 Multi-Node Fleet Accounting

- **Four-Level Piecewise Continuous Physical Validation (`examples/structure/zero_shot_piecewise_validation.py`)**:
  - Paired with [`mindie-sim 0.9.5`](https://github.com/mindie-agent/sim) (`prediction.piecewise` + `prediction.subgraphs`), evaluates measurement-blind per-step latency error and five-category physical diagnoses across L1 operator mechanisms (13 classes), L2 subgraphs (Attention/Indexer, MoE, Normalization & Residual, Hyper-Connections), L3 per-step kernel trace latency, and L4 service TPOT / TTFT.
  - Streams `.csv` / `.csv.gz` kernel traces with interval-union accounting (`union_duration_us`), freezes predictions before reading measured traces, and preserves raw `ttft_ms`, `tpot_ms`, and collective trace distributions without mutation.
- **Hardware Microbenchmark Verification & Cross-Layer Calibration Speedup (`examples/structure/{hardware_microbench_probe,qualified_native_calibration,service_response_acceptance}.py`)**:
  - `hardware_microbench_probe.py` defaults to read-only `--mode verification` and enforces a 1 GiB free-HBM preflight check plus explicit `TimeoutError` propagation in `--mode live-npu`.
  - `qualified_native_calibration.py` caches operator physical axes across identical layers, accelerating 60-layer primitive calibration by over an order of magnitude.
