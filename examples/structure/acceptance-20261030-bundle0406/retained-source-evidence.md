# 04:06 Decode 制品与模型输入清单

实际选择 21 个目录：已固定的 A5 V4.1 3 个、本次 A5 Kimi 6 个、A3 Kimi 四层 5 个、A5 GLMFlash 7 个。V4.1 身份直接复用；其余 18 份源仅流式哈希，不重复全事件解析。

| 组 | 数量 | 声明结构/放置 | Force EPLB 证据 | Prefix / MTP |
|---|---:|---|---|---|
| A5 Kimi | 6 | 93层 expert16-top8，TP8/DP1/EP8 | launch 意图；resolved log 未找到 | APC off / 未配置 MTP |
| A3 Kimi | 5 | 独立4层 checkpoint，TP8/DP1/EP8 | launch 意图；resolved log 未找到 | APC on / 无 MTP 声明 |
| A5 GLMFlash | 7 | 45层 KDA/MLA，TP8/DP1/EP1 | resolved log 明确 true | APC on / 3 drafts，synthetic [.8,.64,.512] |
| A5 V4.1 | 3 | 40层主体前端候选，TP1/DP8/EP8 | resolved log 明确 true | APC off / 未配置 MTP |

GLM 的 measured spec_accept_ratio 独立保留；约 0.65 的整组 accepted/draft 比率不等于首位置 0.8 接收率。prefix queries 为零时 hit ratio 保持未知，不伪称零命中或 100% 命中。

| Case | 源 MiB | Client c | 实际 prompt tokens | Profiled token TPOT P50 ms |
|---|---:|---:|---|---:|
| kimi_k3_tp8_high_conc_decode_c1_p4k | 97.46 | 1 | [4104] | 35.8627 |
| kimi_k3_tp8_high_conc_decode_c2_p4k | 98.52 | 2 | [4104] | 39.2215 |
| kimi_k3_tp8_high_conc_decode_c4_p4k | 94.98 | 4 | [4104] | 42.4884 |
| kimi_k3_tp8_high_conc_decode_c8_p4k | 89.71 | 8 | [4104] | 44.4141 |
| kimi_k3_tp8_high_conc_decode_c16_p4k | 84.78 | 16 | [4104] | 52.4609 |
| kimi_k3_tp8_high_conc_decode_c32_p4k | 79.85 | 32 | [4104] | 69.6635 |
| kimi_k3_w4a8_4layer_tp8_high_conc_decode_c1 | 3.59 | 1 | [4096] | 7.1672 |
| kimi_k3_w4a8_4layer_tp8_high_conc_decode_c4 | 4.02 | 4 | [4096] | 7.4760 |
| kimi_k3_w4a8_4layer_tp8_high_conc_decode_c16 | 4.12 | 16 | [4096] | 8.6278 |
| kimi_k3_w4a8_4layer_tp8_high_conc_decode_c32 | 4.58 | 32 | [4096] | 9.7714 |
| kimi_k3_w4a8_4layer_tp8_high_conc_decode_c64 | 5.38 | 64 | [4096] | 14.1839 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c8_p4k | 40.05 | 8 | [4104] | 14.6037 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c16_p4k | 45.45 | 16 | [4104] | 15.2158 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c32_p4k | 39.48 | 32 | [4104] | 20.3334 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c64_p4k | 33.37 | 64 | [4104] | 29.8283 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c4_p8k | 24.09 | 4 | [8200] | 12.9330 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c16_p8k | 44.47 | 16 | [8200] | 15.5582 |
| glm5_3_flash_w8a8_mxfp8_high_conc_decode_c32_p8k | 38.44 | 32 | [8200] | 25.0499 |

A3 源大小为压缩 CSV 大小，选 tp0；其余 rank 路径保留。客户端 c 不当作 per-rank B，prompt token 不当作每步精确 KV context。额外已落盘的 A5 Kimi p16k 四目录另列，不混入本 21 源覆盖数。
