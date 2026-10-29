# 新增 17 + 9 份 Decode 采集源证据

每份仅选一个原始 rank；gzip 流式读取。启动日志、脚本意图与实测客户端指标分别保留，模型声明缺失时不套用其他模型。

| Case | CSV MiB | 单 rank | Sim 声明 | 运行 force_eplb |
|---|---:|---|---|---|
| qwen35-35b-a3-tp4-c144 | 16.60 | top_level_export | 已配对 | True |
| qwen35-35b-a3-tp4-c320 | 14.14 | top_level_export | 已配对 | True |
| qwen35-397b-a3-tp16-c48 | 20.53 | top_level_export | 已配对 | None |
| qwen35-397b-a3-tp16-c136 | 16.86 | top_level_export | 已配对 | None |
| qwen36-a3-tp4-c64 | 21.23 | top_level_export | 已配对 | None |
| qwen36-a3-tp4-c128 | 18.26 | top_level_export | 已配对 | None |
| qwen38-a3-tp4-c64 | 21.23 | top_level_export | 已配对 | None |
| qwen38-a3-tp4-c128 | 18.23 | top_level_export | 已配对 | None |
| v4flash-a3-tp8-c4 | 16.47 | tp0 | 已配对 | None |
| v4flash-a3-tp8-c8 | 17.88 | tp0 | 已配对 | None |
| glm53flash-a3-tp16-c4-livepre | 11.19 | tp0 | 已配对 | None |
| glm53flash-a3-tp16-c16-livepre | 15.91 | tp0 | 已配对 | None |
| glm53flash-a3-tp16-c2 | 9.93 | tp0 | 已配对 | None |
| glm53flash-a3-tp16-c4 | 10.83 | tp0 | 已配对 | None |
| glm53flash-a5-tp8-c3 | 56.12 | top_level_export | 已配对 | True |
| glm53flash-a5-tp8-c96 | 29.04 | top_level_export | 已配对 | True |
| glm53flash-a5-tp8-c1 | 67.72 | top_level_export | 已配对 | True |
| qwen36-a5-tp2-c12 | 41.46 | top_level_export | 已配对 | None |
| qwen36-a5-tp2-c96 | 19.01 | top_level_export | 已配对 | None |
| qwen36-a5-tp2-c1 | 62.01 | top_level_export | 已配对 | None |
| qwen35-35b-a5-tp4-c32-eager | 77.64 | top_level_export | 已配对 | None |
| qwen35-35b-a5-tp4-c64-graph | 75.78 | top_level_export | 已配对 | True |
| qwen35-35b-a5-tp4-c128-graph | 84.35 | top_level_export | 已配对 | True |
| qwen35-35b-a5-tp4-c8-eager | 67.94 | top_level_export | 已配对 | None |
| qwen35-35b-a5-tp4-c16-eager | 72.58 | top_level_export | 已配对 | None |
| qwen35-35b-a5-tp4-c4-graph | 66.89 | top_level_export | 已配对 | True |

CSV 大小对 gzip 指压缩文件字节；此表不代表完整解压后的事件内存。None 表示尚无该字段的直接启动证据，不等于 False。
Q35 A5 客户端 prefix_cache_reuse_ratio 不是服务端缓存指标；0.0 不解释为零命中。来源配对与原始 checkpoint config 完全同一性分别记录，存在 Sim 声明不表示采集目录保存了原始配置。
