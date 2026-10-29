# A5 高并发 Decode：源证据与自动主体提取

复用外部采集任务已经落盘的六组数据，仅读取每组 rank 0；顶层 CSV 与 prof/rank0 副本 SHA 完全一致，未把两个副本重复统计。
模型结构来自现有 Sim，运行 TP、MTP、图模式与 APC 配置来自保留的 server log。
层边界是结构引导推断；M/B/q 表示张量执行几何，可能含 padding，客户端并发另列。

| 模型 / TP | 客户端 c | 执行 M/B/q | 完整主体 | Body Mean ms | P50 ms | P90 ms |
|---|---:|---|---:|---:|---:|---:|
| Qwen3.6-27B-W8A8 / TP8 | 40 | 160/40/4 | 54 | 20.683911 | 20.611527 | 21.333773 |
| Qwen3.6-27B-W8A8 / TP8 | 128 | 512/128/4 | 38 | 32.608990 | 32.227435 | 33.851394 |
| Qwen3.6-27B-W8A8 / TP8 | 4 | 16/4/4 | 73 | 13.342454 | 13.244635 | 13.484726 |
| Qwen3.8-27B-w8a8-mxfp8-mtp / TP4 | 32 | 128/32/4 | 48 | 22.791335 | 22.711011 | 22.894013 |
| Qwen3.8-27B-w8a8-mxfp8-mtp / TP4 | 128 | 512/128/4 | 29 | 45.689314 | 45.690342 | 45.735162 |
| Qwen3.8-27B-w8a8-mxfp8-mtp / TP4 | 4 | 16/4/4 | 45 | 13.026721 | 13.005325 | 13.166872 |

下面的 TPOT 与上表 Body 使用不同边界。Profiled client 是带采集运行的客户端统计，engine window 是 /metrics 窗口估计；二者均不冒充纯模型主体。

| Case | 未采集 sweep TPOT ms | 带采集 client P50 ms | Engine window TPOT ms | 整体 prefix 命中 | 共享前缀复用 | 窗口 MTP 接收率 |
|---|---:|---:|---:|---:|---:|---:|
| a5_qwen36_highconc_c40 | 10.1376 | 12.8706 | 13.6982 | 99.8051% | 100.0000% | 66.6667% |
| a5_qwen36_highconc_c128 | 14.0233 | 17.5009 | 20.4649 | 99.8051% | 100.0000% | 65.5496% |
| a5_qwen36_highconc_c4 | 6.3813 | 8.0417 | 10.0039 | 99.8051% | 100.0000% | 67.7928% |
| a5_qwen38_highconc_c32 | 10.3671 | 14.1064 | 15.9039 | 87.3294% | 87.5000% | 64.2432% |
| a5_qwen38_highconc_c128 | 24.9952 | 27.8879 | 28.3205 | 87.3294% | 87.5000% | 63.1045% |
| a5_qwen38_highconc_c4 | 8.1964 | 11.0487 | 16.4587 | 87.3294% | 87.5000% | 67.5725% |

MTP 配置为三个位置的 synthetic 接收概率 [0.8, 0.64, 0.512]；实测每 draft token 的汇总接收率不是 0.8。
Qwen3.6 每请求缓存 4096 / 4104 个 prompt token；共享前缀全部复用，8 个唯一 suffix 不命中。Qwen3.8 缓存 3584 / 4104 个 token，共享前缀仅复用 87.5%。
六份 step_trace_time.csv 都只有整窗一行且 Step 为空，不用它构造单步分母。当前每 Forward 精确 KV 长度没有导出，请求 4104 token 仅是条件预测起点。

Ascend950DT_9582 的直接设备属性来自同批独立 kernel-floor capture：32 Cube / 64 Vector，rack06os1。Serving CSV 只导出 Device_id，未伪称六份 CSV 分别直接记录了 SKU。镜像 v0.30.0rc2-a5/c3d00a196905 来自采集摘要；日志验证运行 vLLM 0.30.0、TP4/TP8、DP1、FULL_AND_PIECEWISE 和 APC 开启。

Kernel-floor 的独立审查见 Sim data/verification/a5-microbench-boundary-review-20261030.json（c850dbfd）：完整 kernel Duration 与同 stream 间隔不等于统一 launch 常数；本次未用该微基准改写 runtime。

本轮完整主体 287 个，正事件 659725 条；每个正事件在完整主体、辅助段、拒绝段或尾片段中恰计一次。
源 CSV/SHA、配置日志行、MTP 与 prefix 原始计数、每 case 完整事件分母均保存在 decode-forward-auto-cases.json 与 decode-forward-auto-acceptance.json。

新采集包含 HcclLaunchAicpuKernel controller 跨后继层 norm 的尾部。补齐这个真实 ABI 后，六份采集统一再次提取；只在真实跨层时裁 controller 尾，正常 hcom 与层内 controller 仍保留。
两代提取总耗时 46.642s；完整主体统计与事件分母保持一致，层边界统计按新规则更新。原 30 源历史 generation 未重写。
