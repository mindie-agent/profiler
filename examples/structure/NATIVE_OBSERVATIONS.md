# 原生算子校准与执行条件

`native_observations.py` 是离线 capture 回放的 `observed_native` 输入适配器。
它在现有 `body.predict_body` 之前绑定已声明的物理条件，不修改原始 CSV、
观察摘要或 Body 计时边界，也不向普通 Sim 预测加入测量准入要求。
Wave5 重跑入口和 DSH 新预测使用这个适配器；聚合已有报告不会补写新校准身份。

每次运行分别记录 Sim 内容身份和 native observation 身份。后者覆盖适配器代码、
各硬件导入器和 profile JSON；校准变更不能复用旧预测缓存。profile 内保留训练与
验证来源、原生行号、SHA256、输入 ABI 和尚未确认的条件。未知编译二进制身份
作为限制保留，不冒充已经实测证明的源码等价关系。

## 已实现的边界修正

- A2 LightningIndexer 使用完整 LI 边界；SparseFlashAttention 单独校准。
  匹配包含有序的 query/context 分区和压缩比例，避免相同 pair 数的不同批次混用。
  量化输入按实际角色区分 BF16 indexer、BF16 MLA absorb 和只含 scale 的 INT8 权重列。
  默认 INT8 scale+offset 合同保留，显式声明冲突不会被校准覆盖。
- A2 Prefill 与 q=1 Decode 使用不同 profile。Decode 的 MlaPreprocess 不拆成
  Prefill 的独立矩阵调用。通信响应保留 payload、并行组和 transport 条件，
  不把完整 Body 残差填进每层 AllReduce。
- A5 q=1 GDN profile 只有在五个完整原生边界均匹配时才替换旧规则。
  有效序列、物理形状、调用实现和硬件服务条件共同限定适用域。
  未命中时保留调用者的原始输入与预测路径，不删除真实的 route_normalize。
- A5 q=4 使用独立的 FlashAttention/递归响应，显式区分有效 query 行、
  捕获槽位与零长度填充序列。Qwen3.6 的完整 64K capture 组与 Qwen3.5 的
  完整 192K 组留作验证，其原生耗时不进入训练曲线。
- Qwen3.5 非融合 MC2 调用显式区分有效 group-list 行与分配容量。
  q=28/physical=32 的源 mask 保留 56 行有效专家计算和 256 行接收容量；
  GEMM 按有效行执行，SwiGlu/量化扫描完整容量，并保留 FP32 router 及
  FP32→BF16 权重 scale Cast。导入要求实际命令声明 force-EPLB 开启、
  GMMSwiGLUQuant 融合关闭，显式冲突保留原输入。
- 图捕获描述符区分有效 query 行与捕获的物理行。完整图中的 GDN 拷贝、
  gating 和 Q/K normalization 保留物理缓冲区；重复的末尾序列偏移表示
  零长度槽位，不产生额外卷积或递归状态工作。
- A2/A3/A5 回放从调用者选定 capture 的 `cmd.sh` 导入字面量编译配置。
  不根据模型名或观察耗时猜捕获桶；未声明字段保留为 `not_provided`。
  A3 中已有 188 个 capture 的旧模板桶与真实命令不同，例如实际 q=1
  卷积/递归输入仅一行，旧模板却从另一部署继承了最小 4/8 行捕获桶。

## 为什么整网总误差不能替代逐群验收

旧 Wave5 表中存在把首次等待均摊到普通算子的记录。例如 A3 的
`synth_qwen35_L8_E16_K2_tp8ep8_prefill_4k_c1`，旧 AllReduce 响应为每次 92 ms，
而两个主要空窗实际位于首层 gather/scatter 状态访问之前。总时长可以因此接近，
两个 chunk 的误差却方向相反。新的原生响应只取完整 kernel 观测，不吸收这些空窗。

保留数据还存在相同预测输入、不同运行状态的情况。A3
`qwen38_tp8_mtp3_prefill_192k_c1` 与 `qwen38_tp8_mtp3_prefill_256k_c1`
的第一块均为 q=8192/context=0。两份真实命令均声明完整 Decode 捕获及
`[1,2,4,8,12,16,24,32]` 槽位；导入这些字段后，完整模板与预测几何的
SHA256 仍相同：`11c9b780614a562a0a761978b11f0f60a419365fe366a7fd8e784be76a41b15b`。

| 保留观测 | Body wall (ms) | 设备活动并集 (ms) | 内部空窗 (ms) |
| --- | ---: | ---: | ---: |
| 192K capture 首块 | 3221.954126 | 425.961623 | 2795.992503 |
| 256K capture 首块 | 426.426140 | 425.334521 | 1.091619 |

这些值来自原始 capture 的纳秒区间并集，不能把空窗删去后声称原始 Body 通过。
一个相同输入的单值预测也无法同时落在这两条观测的 ±10% 区间。
需要独立输入首次执行、图重放或编译缓存等状态，并确认等待归属，才能预测这部分差异。
仅有汇总 API 时间或客户端 SSE 到达时间不能恢复逐调用、逐 rank 的状态。

验收同时保留 capture 加权误差、主 population 误差和每个 population/chunk。
算子均值校准通过不代表每次原语调用、全部 Body 或独立泛化已经通过。

## 尚未覆盖的 eager 调用与等待状态

Qwen3.5 q=64 的三个 eager capture 使用 ALLGATHER caller：DP=1、非 SP
条件下保留完整 64 行，按 EP 本地专家筛选，shared/routed 汇合后进行 TP
AllReduce。CSV 有 MoeInitRoutingV3/MoeFinalizeRoutingV2，没有 MC2
Dispatch/Combine。因此这些 capture 不套用上述 MC2 profile，但仍在全量分母中。
现有模板的 MC2 调用不能证明这条 eager 路径已被忠实建模。

39 个完整 forward 中，部分阶段具有较短 AllReduce 和较长内部空窗，后续阶段
则具有较长 AllReduce 和较短空窗。原始等待不能一律归为稳定传输服务或 host
固定开销。保留的 API 表只有累计时间/次数，没有 timestamp、thread 或关联 ID；
host AllReduce 计数为每 forward 90 次，而 target Body 原生调用为 80 次，
因此也不能把该表总时长直接加进每个 target Body。
