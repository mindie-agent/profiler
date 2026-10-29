# Decode 自动主体与分层回放

以下为已有采集的结构引导推断；模型层序列来自 Sim，时间来自原始设备事件，未伪造 Host/module 标记。
每个完整主体必须匹配全部声明层并由词表投影闭合。源 CSV、SHA、完整主体/辅助/拒绝/尾片段事件分母见 JSON。

| Case | 正事件 | 完整主体 | Mean ms | P50 ms | P90 ms |
|---|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 275880 | 152 | 13.134611 | 13.129265 | 13.145059 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 261727 | 145 | 13.291562 | 12.802981 | 12.816588 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 136350 | 75 | 26.328226 | 26.305803 | 26.335546 |

不同请求并发和实际 query/batch 的统计分别保留在 geometry_groups；上表不直接用于混合工况的 Sim 误差判定。

负载均衡、MTP 接收率与 Prefix Cache 命中按 manifest 中的实测或配置证据分别报告；请求长度不冒充每步精确 KV 长度，客户端 TPOT 不冒充单次模型主体耗时。

## V4.1 主体边界解释

40 层主体以末层 HcPost 完成为结束边界，后续 head preparation 和 terminal final norm 排除。c8/c64 还保留独立词表 LMHead；自动提取中的 `auxiliary_or_partial_layer_sequence` 在这里对应这些 0 个 attention anchor 的独立段，并非 MTP 或不完整模型主体。原 manifest 将 c1 的“没有 LMHead”泛化到全部三源，此处明确纠正；原始 hash 与数值不回写。

| Case | 完整主体 | Mean ms | P50 ms | Max ms | 独立 head |
|---|---:|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 145 | 13.291562 | 12.802981 | 82.348968 | 145 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 75 | 26.328226 | 26.305803 | 27.876925 | 75 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 152 | 13.134611 | 13.129265 | 13.848067 | 0 |

c8 的 82.348968 ms 样本保留；activity union 82.253705 ms、内部未覆盖 gap 0.095263 ms，不能称为 Host 调度空泡。单次 MoeDistributeDispatchV3 69.562066 ms 的原始端点证据见 [c8-outlier-task-evidence.json](c8-outlier-task-evidence.json)，其延迟原因未由当前单 rank 采集证明。
