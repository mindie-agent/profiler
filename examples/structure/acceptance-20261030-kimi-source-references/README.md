# Kimi 六类原生算子的完整 ABI 条件参考

12 个 A5 BF16 源、618 次已验收的完整 Body，复用四类定向 native 分桶和原先保留的两类 MC2 完整 ABI。固定运行时为 `18c423c7297fc3b3e92a5eb34f204df40a2a6cb6`，使用 source 配方、logical96 / physical16 MLA 结构。成本阶段没有读取原始 CSV，也没有重做 Body 分段。

[完整报告](kimi-native-reference-scoreboard.json) 包含 384 个条件组、298,518 个已参考事件；六类总人口为 329,394。348 个不同程序集合全部执行成功，12 源正式批次共 19.87 秒，峰值 195.39 MiB。此前 c32 pilot 运行 1.27 秒，只检验接口，不重复计入正式人口。报告中新增三个 importer 投影字段没有改变任何原有 group 数值、成本、直方图或身份；`format_projection` 保留变更前的报告哈希及逐源等价验证。

| c32 p4k，46 次完整 Body | 调用/F | 实测活动 ms/F | Sim 条件 service ms/F | 参考−实测 ms/F |
| --- | ---: | ---: | ---: | ---: |
| MlaPrologV3 | 24 | 0.999866 | 1.102088 | +0.102222 |
| AttnResFwd | 187 | 2.132355 | 1.348694 | −0.783661 |
| CausalConv1d | 69 | 0.754190 | 0.090528 | −0.663662 |
| RecurrentKda | 69 | 2.101811 | 1.034184 | −1.067626 |
| MoeDistributeDispatchV3 | 92 | 3.146125 | 0.251013 | −2.895112 |
| MoeDistributeCombineV3 | 92 | 1.341689 | 0.417752 | −0.923937 |

这些是设备事件活动与独立 source 程序 service 的差，不可相加解释 Body 墙钟，也不证明 bandwidth 或 peer wait。所有新组均为 `reference_only`，严格通过数增加 0。

原生 ABI 与条件边界如下：

- **RecurrentKda**：真实 10 输入/3 输出、BF16 QKV/gate、FP32 beta/state/A_log/bias，没有 accepted-token 数组。一次 native batch 对应 source case 的完整 arch35 recurrent batch 程序，保留序列长度与状态槽条件；不把 flat backing extent 当 active stride。
- **CausalConv1d**：验证 active x、4-tap 权重、历史 state、prefix/slot 描述；对应已有 short-convolution 工作。当前声明仍是通用 elementwise 配方，此参考不证明原生卷积流水已校准。
- **AttnResFwd**：完整六输入/三输出与层拓扑区分 attention、FFN 和 final 调用。每层的 valid-bank/fuse-add/output-norm 等 source 标量可不同，依据已保留的 `layer_counts` 对各物理程序成本加权。实测 native 直方图与 P50 始终完整保留，绝不拆出不存在的逐层测量分布。初始巨大 prefix extent 仅作 backing capacity。
- **MlaPrologV3**：完整 21 输入/7 输出确认 physical16 heads；对应现有 q_a、kv_a、q_norm、q_b、kv_norm、rotary、kv_store、q_absorb 子图。当前没有选择原生融合资源程序，故为含内部 HBM/launch 的未融合参考；不包含随后 Slice/Pad、attention core、V expand、output gate 或 output projection。
- **Dispatch/Combine V3**：原先完整 8/7 与 19/1 ABI 对应 source case 的全部协议阶段、网络阶段和 pack/unpack。层 ID、collective ID 与 stream 的层前缀只在同构成本键中规范化，实际送入 cost engine 的图与 stream 分离保持原样。路由 group counts、有效行数及 peer readiness 仍未观测，完整 buffer 不等于有效计算量。

仍有明确的输入结构差异：B1/B2/B4 的真实 Prolog 输入分别为 `[B,7168]`、Conv 输入 `[B,4608]`，source 声明分别为 M8 与 36,864 元素。对应 7,968 个 Prolog 和 22,908 个 Conv 事件保留 `unresolved`，不能拿 padded M8 冒充实测 active B。其余四类在这些源中可对账；B8/B16/B32 的六类均可对账。

实现入口是 `compare_kimi_native_partitions.py --manifest <source-a5-manifest> --partition-dir <retained-native-partitions> --output-dir <new-arm> --runtime-source-commit <commit>`。逐源子进程预算 180 秒、512 MiB。四项真实证据测试验证完整事件分母、AttnRes 异构权重、KDA accepted-state 分支隔离、MLA physical/logical 头数隔离和 MC2 stream 分离。

[独立审核](kimi-native-reference-independent-review.json) 通过 12,107 项检查，0 失败：包括 384 个完整参考组、30876 个明确未关联事件、348 个程序集合及 72 个 AttnRes 完整桶的权重与 P50。审核不重读原始采集或执行成本，耗时 1.18 秒，峰值 194.59 MiB。
