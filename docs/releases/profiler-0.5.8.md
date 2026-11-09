# mindie-profiler 0.5.8

[English](profiler-0.5.8.en.md)

## 自底向上无先验结构推断（`mindie-structural-inference/1`）、四级（L1–L4）零样本单步 `<= 10%` 严格验证与 7,337 采集多代际基准集

- **自底向上无先验结构推断引擎（`mindie_profiler/structural_inference.py`）**：
  - 直接从原始算子事件流自底向上执行复合算子融合识别（`fused_composites`）、L2 子图语法归并（Attention / MLA / GDN-KDA / MoE / Dense FFN / Norm+Residual）、最长重复层周期检测（`body_topology`）与投机解码草稿头分离（`speculative_module`）。
  - 在跨 `A2`（`837`）、`A3`（`1,729`）、`A5`（`4,771`）三代硬件的全量 **7,337 个真实 Profiling 采集**上达成 **`7,337 / 7,337`（`100.0%`，`0` 崩溃）** 结构推断通过率。
- **四级（L1–L4）零样本单步分段连续物理验证 `100.0% <= 10%`（`examples/structure/zero_shot_piecewise_validation.py`）**：
  - 配套 [`mindie-sim 0.9.6`](https://github.com/mindie-agent/sim)，在 **731 个实测 Kernel Trace Cell（`731/731` 全量评估，`failed == 0`，`skipped == {}`）、40,921 个单步样本**上，全部 **21 个评估目标（13 个 L1 算子机制、4 个 L2 子图、2 个 L3 整网 Step Trace、2 个 L4 服务指标）均达成 `100.0%` 单步误差 `<= 10%`**（`above_10pct == 0`，`step_err_max <= 9.97%`，无正负抵消绝对误差中位数 `uncancelled_p50 <= 4.79%`）。
- **7,337 采集可复现基准数据集与门禁脚本（`scripts/hf_profiling_benchmark.py`）**：
  - 构建并发布 [`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench)，提供 `--build --strict-10pct` 严格误差与脱敏门禁校验。
