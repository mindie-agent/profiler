# mindie-profiler 0.5.7

[English](profiler-0.5.7.en.md)

## 四级分段连续物理零样本验证（L1–L4）与 A5 多机全家族实测核算

- **四级分段连续物理零样本验证管线（`examples/structure/zero_shot_piecewise_validation.py`）**：
  - 配套 [`mindie-sim 0.9.5`](https://github.com/mindie-agent/sim) 的 `prediction.piecewise` 与 `prediction.subgraphs` 求解器，对 L1 算子机理（13 类）、L2 融合子图（Attention/Indexer、MoE、归一化与残差、超连接）、L3 单步 Kernel Trace 耗时与 L4 服务级 TPOT / TTFT 执行测量盲（measurement-blind）单步误差评估与五类物理归因诊断。
  - 流式解析 `.csv` / `.csv.gz` 核函数明细，计算多流区间并集耗时（`union_duration_us`），并在预测冻结后再加载实测 Trace，严格保持实测 `ttft_ms`、`tpot_ms` 与集合通信原始分布不可变。
- **硬件微基准验证与跨层原语校准加速（`examples/structure/{hardware_microbench_probe,qualified_native_calibration,service_response_acceptance}.py`）**：
  - `hardware_microbench_probe.py` 默认使用离线只读 `--mode verification` 验证模式，在 `--mode live-npu` 下强制执行 1 GiB 可用 HBM 预检与 `TimeoutError` 显式上抛。
  - `qualified_native_calibration.py` 按算子配方缓存同构层物理特征轴，将 60 层大模型原语校准耗时降低一个数量级以上。
