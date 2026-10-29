# Decode 自动主体与分层回放

以下为已有采集的结构引导推断；模型层序列来自 Sim，时间来自原始设备事件，未伪造 Host/module 标记。
每个完整主体必须匹配全部 40 个声明层，以源声明的 mHC collapse 后 FinalNorm 闭合。后续 LMHead 不属于此主体范围；A3 的 3 层 DSpark 辅助结构单独记录。源 CSV、SHA、完整主体/辅助/拒绝/尾片段事件分母见 JSON。

| Case | 正事件 | 完整主体 | Mean ms | P50 ms | P90 ms |
|---|---:|---:|---:|---:|---:|
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 188270 | 76 | 48.584335 | 49.790625 | 50.387173 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 189161 | 77 | 55.010725 | 51.589489 | 54.994841 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 180982 | 78 | 48.615808 | 46.860134 | 47.666347 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 189424 | 76 | 61.402914 | 58.826265 | 61.873344 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 185158 | 77 | 50.095674 | 48.240136 | 48.613229 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 132860 | 73 | 27.285973 | 27.265820 | 27.290260 |

不同请求并发和实际 query/batch 的统计分别保留在 geometry_groups；上表不直接用于混合工况的 Sim 误差判定。

负载均衡、MTP 接收率与 Prefix Cache 命中按 manifest 中的实测或配置证据分别报告；请求长度不冒充每步精确 KV 长度，客户端 TPOT 不冒充单次模型主体耗时。

本批共保留 457 个完整主体、30 个实际执行几何桶；A3 的 384 个 target 主体与 400 个三层辅助段逐一验证互不相交。16 个大 query 或 mixed-query target 序列不纳入 decode 主体，仍保留原事件分母。A5 c128 的 73 个独立词表投影位于 FinalNorm 之后，不当作 MTP 或层切分失败。

A3 只在每次 Attention query 与源声明的 TP4 FlashComm 分片关系核验通过时推导 query/batch：`query_rows = hidden_rows_per_shard × 4 = sequences_per_replica × 8`。请求并发、DP 数和 DispatchFFNCombine 的容量缓冲区都不代替执行 batch。原始较长样本全部保留；例如 c4 首主体为 194.077022 ms。

成本对照选每源调用次数最多的几何桶，覆盖 225/457 个主体；其余 24 个桶明确标记为待预测。A3 原生 fused MC2/FlashComm 仍采用部分解析模型的条件对照，不把低 Body 误差解释为全部原生执行机制已验证。
