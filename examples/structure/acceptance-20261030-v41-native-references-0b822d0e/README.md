# V4.1 输出矩阵、RoPE 与 cache insertion 条件账单

复用七份 A5 TP1/DP8/EP8 rank0 采集的 830 次完整 40 层 Body。一次本地流式补读保留了三族的全部 182,600 个事件 ABI、整数 ns 直方图和层/Forward 归属；全部旧 Body 端点与原家族直方图严格相等。不是新真机采集，也没有重选较快的 Forward。原始流式解析共 70.15 秒、峰值 100.95 MiB。

[完整 ABI 分桶与源角色证据](../acceptance-20261030-v41-native-partitions/)独立审核 18,573 项通过。固定 `0b822d0e` 只重算现有 Sim 程序，成本阶段 32.74 秒、峰值 481.45 MiB、零原始采集重读。63 个条件程序组覆盖 83,000 个事件；99,600 个未覆盖事件完整保留。[账单 JSON](v41-native-reference-scoreboard.json) 的 schema 为 `mindie-native-body-reference-batch/1`，可直接进入统一主表；[算术与人口独审](v41-native-reference-independent-review.json) 2,493 项通过。

| 每 Forward 的真实调用 | 次数 | 当前对应 |
|---|---:|---|
| TransposeQuantBatchMatMul | 40 | `grouped_output_a / wo_a`，attention 之后的输出投影 |
| KvCompressEpilogV2 | 40 + 4 | window packed cache store + source-owned compressed cache store |
| InplacePartialRotaryMul | 8 + 4 + 4 | index query、index key、compressed KV |
| InplacePartialRotaryMul | 40 + 40 | Q 与 KV 两次真实调用；旧结构只有一个合体 rotary 程序，不能重复分配两份成本 |
| InplacePartialRotaryMul | 40 | attention 输出 inverse RoPE；当前结构缺少独立节点 |

`TransposeQuantBatchMatMul` 的完整实际 ABI 是 `[B,8,4096] × [8,4096,1024] → [B,8,1024]`，含 FP8 输入/权重和 E8M0 尺度；独立源调用是 `wo_a`，不是输入 `w_uk`。B1 至 B16 的实测 Mean 为 18.924–21.093 us，现有程序参考 8.411–8.638 us；此前单独执行的 DynamicMxQuant 不再加入此矩阵预算。

Window cache 每次实测 Mean 为 3.146–6.379 us，现有资源参考 1.312 us。Compressed cache 的 320-byte packed 行与 window 的 544-byte 行分别验证；slot mapping 值和实际有效压缩行没有保存。`context=2048,q=1` 的 ratio-2 声明没有新完成的压缩行，因此部分程序的真实声明工作量为零、参考值为零。这是可见的声明/有效行条件差异，不是失败返回零，也不能拿保留输入容量当有效写入数补 FLOPs 或流量。

所有参考均为 `reference_only`，`additional_budget_allowed=false`，没有增加 strict 比较或通过数。三族的活动差额不可相加解释 Body wall span。Q/KV 拆分与 inverse RoPE 仍等待独立的 source-only 结构能力；当前没有用现有合体程序制造这 120 次/F 的一对一覆盖。
