# mindie-profiler 0.5.14

[English](profiler-0.5.14.en.md)

本版本配套正式发布的 [`mindie-sim 0.9.14`](https://github.com/mindie-agent/sim/releases/tag/v0.9.14)，在完整保留 `0.5.12` CANN 9.x 稳态采集、C7 集合通信就绪核算、原生调用边界（`BIND1`）关联与活跃流水线 PMU 测量供给的基础上，新增单算子 C-ABI 目录查询（`inspect-op`）、内容寻址单算子独立复现器（`repro-op`）、集群互联探测生成与校核（`fabric-probe`）、单算子理论物理下界与双层 Roofline 标注（`op-formula`）以及 `ACLGraph` 多流 DAG 与重叠度分级诊断；历史采集与全量精度基准不重标为本版本的新测量：

- **昇腾算子 C-ABI 目录检索与分页检视（`mindie-profiler inspect-op`、`mindie_profiler/op_api_registry.py`、`mindie_profiler/op_api_paging.py`）**：
  - 内置经版本固定的 CANN `aclnn` 与融合自定义算子 C-ABI 槽位目录（`op_api_catalog.json`），支持按算子名、CANN 版本与槽位区间查询输入张量、标量属性、Workspace 及有效词元维度语义，输出有界 `mindie-op-abi-inspect/1` 回执并暴露 MCP 工具规格。
- **内容寻址单算子独立复现包生成（`mindie-profiler repro-op`、`mindie_profiler/repro_*.py`、`mindie_profiler/op_abi_*.py`）**：
  - 将实测捕获的单算子发生记录（`--occurrence`）严格绑定到固定 ABI 槽位签名，生成携带 `sha256:<64-hex>` 内容摘要的自包含 `repro.py` 单算子复现脚本与确定性输入张量构造规格（`mindie-op-repro-receipt/1`），与 `mindie-sim diff-trace` 输出的 Top 偏差算子复现命令直接闭环。
- **多机集群互联微基准生成与回执校核（`mindie-profiler fabric-probe`、`mindie_profiler/fabric_probe*.py`）**：
  - 支持 `--emit-script` 按拓扑参数生成零外部依赖的多卡 HCCL 延迟/带宽微基准探测脚本，并通过 `--parse-receipt` 校验实测探测输出，产出可直接注入 `mindie-sim` Mode B（`CalibratedFabricProfile`）的 `mindie-fabric-probe/1` 互联供给回执。
- **单算子理论物理下界与双层 Roofline 标注（`mindie-profiler op-formula`、`mindie_profiler/op_formula_*.py`）**：
  - 复用 `mindie_sim.op_formulas` 代数引擎计算单算子或批量算子明细的精确 FLOPs、访存字节数、硬物理下界与实测供给校准下的参考下界（`mindie-op-formula-mcp/1`），优先拦截低于硬物理下界的测量/归因异常。
- **`ACLGraph` 捕获/重放依赖图重建与多流重叠诊断（`mindie_profiler/aclgraph_*.py`）**：
  - 重建 `ACLGraph` 捕获与重放阶段的跨流事件依赖 DAG（`reconstruct_aclgraph_dag`），对多流串行化与重叠损失执行五级根因定界（`diagnose_aclgraph_overlap`），并核算昇腾硬件 SQ/CQ 任务队列容量预算与 SuperKernel 设备侧循环融合可行性。
- **结构映射入口加固、统一配置常量治理与并行测试提速（`mindie_profiler/structure_mapping.py`、`mindie_profiler/profiler_configs.py`）**：
  - 对 `StructureTargets` / `StructureMapper` 元数据读取施加显式字节预算与载体快照隔离，保留 `native-call-binding/1` 与 HCCL 区间并集去重；收敛超时、采样与阈值常量至 `profiler_configs.py` 并配套静态魔数门禁检查。
