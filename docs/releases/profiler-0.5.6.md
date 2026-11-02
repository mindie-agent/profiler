# mindie-profiler 0.5.6

[English](profiler-0.5.6.en.md)

## Profiler-to-Sim 反向校准桥接导出与 xLLM / MindIE-SD 一等公民框架支持

- **Profiler-to-Sim 反向校准桥接导出（`mindie_profiler/sim_bridge.py`）**：
  - 新增 `export_sim_calibration` 与 `export_sim_case`，支持将实测 `msprof` 剖析摘要、算子族耗时分布与多卡通信统计直接导出为 `mindie-sim` 校准载荷与确定性 Case 定义，并在 CLI 入口暴露反向桥接子命令。
- **xLLM 与 MindIE-SD 一等公民框架采集与显存日志解析**：
  - 在 `mindie_profiler/collect.py`、`mindie_profiler/framework_capture.py`、`mindie_profiler/memory_logs.py` 与 `mindie_profiler/memory_profile.py` 中新增对 `xllm` 与 `mindie-sd`（`mindiesd`）框架进程的受控采集、框架级 Trace 捕获及显存池（如 `xTensor` 物理页池与 DiT 激活/VAE 显存）日志解析支持。
