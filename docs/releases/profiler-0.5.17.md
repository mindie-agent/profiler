# mindie-profiler 0.5.17：SSOT 统一至 `mindie-sim 0.9.19`、闭式子图效率归因与多窗口 PMU / Step 溯源加固

[English](profiler-0.5.17.en.md)

`mindie-profiler v0.5.17` 与 `mindie-sim v0.9.19` 正式配对，移除约 2,890 行重复定义，并将模型目录几何、昇腾 SKU 硬件规格与观测通信/算子契约直接委托给单一事实源：

- **SSOT 统一，移除约 2,890 行重复定义**：模型目录几何（`sim_bridge_catalog.py`）、Ascend SKU 硬件峰值与拓扑（`hardware_presets.py`）以及观测通信、融合、量化、布局与算子契约（`body_*_contracts.py`、`tensor_contracts.py`、`structure_*`）不再维护 profiler 本地副本，全部直接委托 `mindie-sim v0.9.19` 的 `mindie_sim.model_catalog`、`mindie_sim.backends.ascend.profiles()` 与 `mindie_sim.observed_contracts`。转发模块采用 PEP 562 `__getattr__` 惰性 shim：顶层导入不触达 `mindie_sim`，保持 `python -I` 干净与零 NPU 上下文。
- **闭式子图效率归因**：结构导出接入共享 `mindie_sim.subgraph_math`（`algebraic_cube_flops`、`algebraic_vector_ops`、`minimal_boundary_hbm_bytes`），由 `evaluate_subgraph_efficiency` 依据实测 cohort `busy_union_ns`、调用次数与声明硬件峰值直接计算子图 Cube / Vector / HBM 效率；缺少完整 cohort 或硬件峰值时诚实返回 `declared_only` / `unavailable`，不回退本地公式。
- **多窗口 PMU 隔离与 Track 3 Step 溯源加固**：`_prime_pmu_cache` 先按合并排序后的不相交窗口跨度收集 `globalTaskId`，窗口间空隙中的任务不再计入 PMU 扫描预算；小集合在 SQL 内以 `IN (...)` 让 SQLite 下推过滤，并复用统一的 400-ID 上限。CSV `--auto-step` 要求显式 Step 起始时间戳（`Step Start Time(us)`），不再由 Step ID 伪造窗口原点；关联包含扫描改为保持输入顺序的精确 max-end 线段树，避免二次复杂度。
