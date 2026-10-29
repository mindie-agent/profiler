# Qwen3.6 TP8 c4 首层边界核查

只读原始 rank 0 CSV 至 row_index 4717，保留前三次首层及其前后局部片段；完整原始字段、整数 ns、task/stream/CSV locator 见同名 JSON。未重扫六份源，也未修改实测时间。

| Forward | Layer 0 span ms | 实际 device/HCOM union ms | 未覆盖 us | HCOM union ms |
|---|---:|---:|---:|---:|
| auto:0 | 6.446338 | 6.441221 | 5.117 | 6.307867 |
| auto:1 | 2.213801 | 2.208792 | 5.009 | 2.078585 |
| auto:2 | 1.989498 | 1.984399 | 5.099 | 1.849928 |

第一段 6.284378ms 长通信从首层起点后 100.956us 开始：CSV line117 的实际 AivKernel，Task575800、Stream6847。此前 line116 是 GDN output MatMulV3（[16,768] → [16,5120]）；通信之后继续该层 FFN gate_up/down 与第二次 all-reduce，再进入下一层。
line118 是同起止的 hcom 摘要副本，区间并集只计一次。前一 Embedding 阶段的 HCOM 在本体起点之前 3916.825us 已结束，未计入 Layer 0。
后两次同一物理 task 的首个 all-reduce 分别为 2.056230ms、1.826500ms，同样在该层 GDN 输出与 FFN 之间。这些长时段属于本层的真实通信区间，不能作为跨界 wrapper 或 Host 空泡直接删除。
单 rank 无法进一步把通信区间拆成对端等待、网络搬运或 Host 调度诱发的等待；保留这个证据限制。三个局部 union/gap 与新增 core 的结果逐 ns 一致。
