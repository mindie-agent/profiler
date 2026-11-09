# mindie-profiler 0.5.8

[中文](profiler-0.5.8.md)

## Bottom-Up Prior-Free Structural Inference (`mindie-structural-inference/1`), Four-Level (L1–L4) Zero-Shot `<= 10%` Validation & 7,337-Capture Multi-Tier Benchmark

- **Bottom-Up Prior-Free Structural Inference Engine (`mindie_profiler/structural_inference.py`)**:
  - Reconstructs fused operator composites (`fused_composites`), L2 subgraph grammar blocks (Attention / MLA / GDN-KDA / MoE / Dense FFN / Norm+Residual), repeating layer-stack periodicity (`body_topology`), and speculative draft heads (`speculative_module`) directly from raw operator streams.
  - Verified across all **7,337 real profiling captures** (`A2: 837`, `A3: 1,729`, `A5: 4,771`) with **`7,337 / 7,337` (`100.0%`, `0` crashes)** structural inference pass rate.
- **Four-Level (L1–L4) Zero-Shot Per-Step Piecewise Validation at `100.0% <= 10%` (`examples/structure/zero_shot_piecewise_validation.py`)**:
  - Paired with [`mindie-sim 0.9.6`](https://github.com/mindie-agent/sim), evaluates all **731 real kernel-trace cells (`731/731` evaluated, `failed == 0`, `skipped == {}`) and 40,921 per-step samples** across **21 L1–L4 targets**, achieving **`100.0%` pass within `<= 10%` error** (`above_10pct == 0`, `step_err_max <= 9.97%`, `uncancelled_p50 <= 4.79%`).
- **7,337-Capture Reproducible Benchmark Dataset & Gate (`scripts/hf_profiling_benchmark.py`)**:
  - Builds and publishes [`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench) with `--build --strict-10pct` strict accuracy and redaction gates.
