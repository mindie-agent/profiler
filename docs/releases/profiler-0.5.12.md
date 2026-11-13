# mindie-profiler 0.5.12

[English](profiler-0.5.12.en.md)

本版本配套正式发布的 [`mindie-sim 0.9.11`](https://github.com/mindie-agent/sim/releases/tag/v0.9.11)，落地 C7 集合通信就绪上下文提取、HCCL 与原生调用边界（`BIND1`）关系键关联、PMU 活跃流水线测量供给（`mindie-profiler-measured-supply/1`）及 Decode 前向窗口活跃事件有界内存池；历史采集与全量精度基准不重标为本版本的新测量。

- **集合通信就绪提取（`mindie-profiler/collective-readiness/1`）**：新增 `read_collective_readiness` 与 C7 `collective_readiness` 字段，在受保护只读 SQLite 连接与超时预算下通过真实 `TASK.taskType` / `globalTaskId` / `connectionId` 关系键关联 `COMMUNICATION_OP`、`COMMUNICATION_TASK_INFO` 与 `COMMUNICATION_SCHEDULE_TASK_INFO`，按 `(rank_id, communicator, collective)` 输出调用序号，并在缺失因果前驱时保持显式 `unknown`。
- **原生调用边界（`BIND1`）与 HCCL 同调用去重**：`StructureTargets` 与 `StructureMapper` 原生消费 `mindie-sim/native-call-binding/1` 签名与 HCCL Rank 本地关系键别名，兼容新旧 `graph_id` 封签；全窗口独立于 `mapping_limit` 使用区间并集（Interval Union）去重同一 HCCL 调用的 `COMPUTE_TASK_INFO` 与 `COMMUNICATION_OP` 双重表象，CSV 或无 `connectionId` 表结构保持诚实 `unresolved`。
- **PMU 活跃流水线测量供给与稀疏注意力 MTE1 服务速率**：新增 `--aic-count`、`--deployment-image-id` 与 `--sparse-geometry`，基于算子活跃流水线耗时（绝不使用算子端到端耗时）导出纯测量矩阵双负载供给（`mindie-profiler-dual-load/1`）与已鉴权 R64 `KvQuantSparseFlashAttention` 关键 Owner MTE1 服务速率（`mindie-profiler-resource-service/1`）；未声明硬件容量、R35/裸 CSV、镜像摘要冲突或状态异常时均以显式 `limitations` 诚实报告。
- **有界内存与跨平台根目录隔离**：`auto_segment_decode_forwards` 将在途事件投影到轻量活跃记录并在窗口闭合时释放高基数字符串/Shape 池，严格保持 $O(\text{Active State})$ 工作集；Rank 目录推断以传入 `--root` 为硬边界，彻底隔离父级临时目录名称。
