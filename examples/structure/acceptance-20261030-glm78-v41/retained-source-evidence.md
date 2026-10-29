# 新 GLM78 W4A8 与 V4.1 保留制品

三份 GLM CSV 均与对应 tp0 压缩原件逐字节一致；三次源 SHA 不同。16 rank 路径完整保留，仅选择 tp0 分段，未把 16 rank 重复计入模型主体。

| GLM 采集 | CSV MiB | Profiled client TPOT P50 ms | Rank 数 |
|---|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2 | 58.63 | 76.3994 | 16 |
| a3_glm53_w4a8_tp16_tpot50_c2 | 64.92 | 76.1849 | 16 |
| a3_glm53_w4a8_tp16_tpot88_c8 | 72.27 | 89.4419 | 16 |

实际 checkpoint 是 GLM-5.3-W4A8-INT；served-model-name 中的 glm53f 不表示新版 45 层 Flash。保留启动脚本声明 TP16/EP16、DP1、INT8 KV、5-token MTP、synthetic 接收率及 force EPLB；交付目录未保留 resolved 启动日志，配置声明和实际负载均衡仍分列。

V4.1 六组为客户端性能制品：启动日志确认 DeepseekV41ForCausalLM、TP4/DP4、EP enabled、DSpark7。12 个 AISBench 数据库仅有 numpy_store/sqlite_sequence，两份 vllm tar 中没有设备 profiling。Body/层耗时保持缺失，不用 V4Flash 替代。

| V4.1 场景 | Input tokens | Client c | Baseline / Candidate TPOT mean ms | Prefix hit |
|---|---:|---:|---:|---:|
| perf-prefix | 65536 | 16 | 12.6 / 12.7 | 98.8281% |
| perf-prefix-128k-b32 | 131072 | 32 | 17.9 / 17.9 | 98.9258% |
| perf-prefix-128k-b64 | 131072 | 64 | 26.4 / 27.8 | 98.9258% |
| perf-prefix-256k-b64 | 262144 | 64 | 44.3 / 44.8 | 98.9746% |
| perf-prefix-512k-b64 | 524288 | 64 | 89.3 / 90.1 | 98.9990% |
| perf-prefix-b32 | 65536 | 32 | 15.2 / 15.3 | 98.8281% |

Prefix hit 按四个 DP 的 hits/queries 独立复核；约 98.8%–99.0%，没有伪称 100%。TPOT 保持客户端指标，不当作单次模型 Forward 或纯算子耗时。完整原始路径、源 SHA、边界缺口与远端绝对符号链接见 JSON。
