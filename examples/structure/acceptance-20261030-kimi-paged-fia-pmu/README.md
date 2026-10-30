# Kimi FIA 完整 ABI 与同一次读取的 MC2 PMU

本轮只读取既有 12 源、618 次已验收 Body 的局部窗口，不重新采集或定义 Body。通过 `collect_kimi_matrix_partitions.py --retain-pmu`，同一次流式扫描保留 FIA 的完整 31 输入/2 输出 ABI，以及 Dispatch/Combine V3 的原始 PMU 字段。

[读取回执](native-partition-receipt.json) 共 60 个 ABI/拓扑桶：FIA 14,832 次、Dispatch 56,856 次、Combine 56,856 次。三族全部整数时长直方图均与原已保存观测完全相等。12 次流式解析、12 次内容哈希读取，合计 170.34 秒，峰值 190.11 MiB；每个源解析到最后一个已选 Body 的 head 后停止。

FIA 的非空输入槽为 0/1/2/6/14/24/25，分别保留 Q、K/V cache、实际长度数组描述、block table、Q rope 和 rope cache；其余空槽的 shape/dtype/format 原样保存。`B×16×1×512` Query、16 physical heads、128-token page 与 `16×B×1×512` 主输出均来自完整人口，未从两个样例外推。数组的数值没有被采集：block-table 容量不证明有效 K，实际 KV 长度、页面内容与 mask/layout 标量仍未知。

每个桶的 `raw_pmu` 包含：

- 每个实际存在的 AIC/AIV/cube、duration/wait、Block/Mix 列的 present、non-NA、numeric、invalid、zero 与 missing 计数；完整数值直方图与 Mean/P50/P90/min/max 保持 exporter 原单位。
- Accelerator Core、OP State、Block/Mix、device/stream/model/context 的完整分布。
- 前两个与耗时最长五个调用的复合 event ID、原 CSV 行号、Task/Stream/Device ID、时间以及原字段。Task ID 不作为唯一 occurrence 身份；高尾调用没有裁剪。

`N/A` 与测得的 0 分别保留。管道计时可能重叠，高 scalar 占比不能直接解释为网络等待或 peer skew。PMU 字段只增加设备活动证据，不改变已验收 Body 的 span/activity/gap。

这次保留的 case/结构声明来自 `5251d0d5` 的 `kimi-source-paged-host`，用于复核层拓扑。它没有产生新预测：该代 host dispatch 使用 nominal context 4096/16384，而现有 accepted-case 对账条件为 4104/16392；同时 FIA source 节点尚无可用的导出 contract/physical_work。这些已知问题不能通过减去 8 或放宽检查隐藏。完整原始 ABI/时长不依赖其成本声明；后续在独立稳定输入下重新核验 source 程序。

可选 PMU 模式直接调用共享 `decode_csv_row`；没有复制事件解码逻辑或修改 profiler 核心源适配器。两个基于真实三行 capture 的测试验证解析身份一致、NA/zero 分离、重复 Task ID 的复合身份和完整耗时尾部保留。

[独立审核](native-partition-independent-review.json) 通过 34,857 项检查、0 失败，覆盖完整直方图/Body 身份、FIA 的 NBS 输出布局、Decimal 分位统计、NA/zero 分母和耗时最长调用的原始定位。审核耗时 1.73 秒，峰值 119.20 MiB，不重读原始采集或计算成本。[MC2 汇总](mc2-pmu-summary.md) 独立展示相同人口的 PMU 与前一代条件资源参考。
