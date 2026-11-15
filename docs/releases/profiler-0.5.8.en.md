# mindie-profiler 0.5.8

[中文](profiler-0.5.8.md)

> [!NOTE]
> **Archival Note (Evidence Boundary Correction)**: This document is retained as historical context for the `v0.5.8` release. Subsequent auditing established that `7,337` denotes registered manifest entries rather than independently validated captures, and that the historical all-row `100.0% <= 10%` (`731/731`, `21/21`) artifact figures relied on target-derived predictor inputs rather than independent accuracy evidence. See [`README.en.md`](../../README.en.md#benchmark-inventory--evidence-boundary) for the authoritative evidence boundary and current validation entrypoints.

## Bottom-Up Prior-Free Structural Inference (`mindie-structural-inference/1`), Four-Level (L1–L4) Validation Entrypoint & Multi-Generation Benchmark Manifest

- **Bottom-Up Prior-Free Structural Inference Engine (`mindie_profiler/structural_inference.py`)**:
  - Reconstructs fused operator composites (`fused_composites`), L2 subgraph grammar blocks (Attention / MLA / GDN-KDA / MoE / Dense FFN / Norm+Residual), repeating layer-stack periodicity (`body_topology`), and speculative draft heads (`speculative_module`) directly from raw operator streams.
  - Verified crash-free execution across all `7,337` registered manifest records (`A2: 837`, `A3: 1,729`, `A5: 4,771`; `0` crashes).
- **Four-Level (L1–L4) Per-Step Piecewise Validation Script (`examples/structure/zero_shot_piecewise_validation.py`)**:
  - Paired with [`mindie-sim 0.9.6`](https://github.com/mindie-agent/sim), introduces the 21-target L1–L4 evaluation harness spanning 13 L1 operator mechanisms, 4 L2 subgraphs, 2 L3 forward timelines, and 2 L4 service metrics (the initial `v0.5.8` historical artifact reported `above_10pct == 0` across `731` entries and `40,921` step samples; run `--no-historical` for independent evaluation without historical backfill, as documented in `README.en.md`).
- **Benchmark Dataset Builder & Redaction Gate (`scripts/hf_profiling_benchmark.py`)**:
  - Publishes [`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench) with `--evaluate --strict-10pct` manifest scoring and redaction gates.
