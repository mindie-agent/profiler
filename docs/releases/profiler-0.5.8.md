# mindie-profiler 0.5.8

[English](profiler-0.5.8.en.md)

> [!NOTE]
> **归档说明（证据边界更正）**：本文档作为 `v0.5.8` 历史发布说明归档保留。后续独立审计确认，早期基准工件中的 `7,337` 为登记清单条目数（并非独立精度覆盖数），且历史汇总表中的全量 `100.0% <= 10%`（`731/731`、`21/21`）混入了由实测目标反向派生的输入特征，不构成独立精度证明。当前权威证据边界与分级验证准则请以仓库主文档 [`README.md`](../../README.md#基准数据集清单与独立精度证据边界) 为准。

## 自底向上无先验结构推断（`mindie-structural-inference/1`）、四级（L1–L4）分段验证入口与多代际基准清单

- **自底向上无先验结构推断引擎（`mindie_profiler/structural_inference.py`）**：
  - 直接从原始算子事件流自底向上识别复合融合算子（`fused_composites`）、归并 L2 子图结构块（Attention / MLA / GDN-KDA / MoE / Dense FFN / Norm+Residual）、检测最长重复层周期（`body_topology`），并分离投机解码草稿头（`speculative_module`）。
  - 在横跨 `A2`（`837`）、`A3`（`1,729`）、`A5`（`4,771`）三代硬件的 `7,337` 条登记清单记录上完成无崩溃执行验证（`7,337 / 7,337` 运行完成，`0` 崩溃）。
- **四级（L1–L4）单步分段验证脚本（`examples/structure/zero_shot_piecewise_validation.py`）**：
  - 配套 [`mindie-sim 0.9.6`](https://github.com/mindie-agent/sim) 提供覆盖 13 项 L1 算子机制、4 项 L2 子图、2 项 L3 整网前向时间线与 2 项 L4 服务指标的分段评估脚本（`v0.5.8` 初始发布工件曾在 `731` 个条目、`40,921` 个单步样本上记录 `above_10pct == 0`；独立无回填评估请使用 `--no-historical` 入口，详见主 `README.md`）。
- **公开基准清单构建与脱敏门禁脚本（`scripts/hf_profiling_benchmark.py`）**：
  - 构建并发布公开数据集 [`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench)，提供 `--evaluate --strict-10pct` 清单核验与敏感字段脱敏门禁。
