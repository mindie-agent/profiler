# Decode Forward 边界证据回放

复用本地历史 A5 Qwen3.6 TP8 的 8 份完整导出；本次没有真机补采。
设备 MODEL_EXECUTE / MODEL_WAIT_COMPLETE 可给出 graph execution envelope，本文件仅记录这些设备标记直接支持的边界，body_forward_span_ms 和 per_layer_ms 不直接由图长短赋值。

后续 [结构引导自动回放](decode-forward-auto-acceptance.md) 将完整模型层序列和 LMHead 契约闭合，再与这里的图窗口逐一交叉核验；自动推断的主体/层耗时在那里呈现。

| Case | 请求长度 | 请求并发 | 图窗口 | 未配对 marker |
|---|---:|---:|---:|---:|
| a5_qwen36_p126976_c1_hold | 126976 | 1 | 242 | 0 |
| a5_qwen36_p126976_c4_hold | 126976 | 4 | 352 | 0 |
| a5_qwen36_p16384_c1_hold | 16384 | 1 | 342 | 0 |
| a5_qwen36_p16384_c4_hold | 16384 | 4 | 362 | 0 |
| a5_qwen36_p4096_c1_hold | 4096 | 1 | 364 | 0 |
| a5_qwen36_p4096_c4_hold | 4096 | 4 | 338 | 0 |
| a5_qwen36_p65536_c1_hold | 65536 | 1 | 274 | 0 |
| a5_qwen36_p65536_c4_hold | 65536 | 4 | 366 | 0 |

图窗口覆盖执行发起到设备完成，保留图内通信与等待，仅自然剥离图间空泡。Model ID 的时间包含关系只作辅助证据，不把较长图认定为主体、较短图认定为 MTP。

同批启动日志明确 prefix caching=false；强制负载均衡、0.8 接收率与 DSpark 未有制品证据。客户端 input_len/concurrency 只描述请求，不填作每次 Forward 的实际 KV 长度和活跃 batch。

A3 Qwen3.5 的 `qwen35-gdn/PROVENANCE.md` 明确只保留导出 CSV；A5 `qwen38-c8/MANIFEST.md` 明确 DB/task_time 未取回。已有 sampler/gdn-gap 分段结果不作为精确层边界。

复跑：`PYTHONPATH=. python examples/structure/replay_decode_graph_evidence.py`。

辅助 graph 分位数沿用 accounting 的 `sorted_values[round(p*(n-1))]`（Python round、不插值）；主体报告使用 median P50 / 最近秩 P90，两者方法明确分开，未改写已完成主体回放的计时。
