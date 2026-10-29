# 后续 13 个 Decode 采集输入

与上一批 21 源分开保留身份：新增 V4.1 c4/c16/c32 p2k 三源、Kimi p16k 六源、A3 GLMFlash ACLGraph 四源，共 13 个。没有重读上一批原始 CSV。

A3 GLM 交付目录只保留导出的 CSV，benchmark 与 16-rank manifest 在 workstream 的同名 deliverables 下。已验证交付 gzip 与原 tp0 gzip 同 SHA，解压内容与当前 CSV 同 SHA，因此元数据关联有字节级证据。

其启动脚本改为按 token 计的捕获桶 [6,12,24,36,48,72,96,144,192,288,384]，MTP5 的 q6 可覆盖到 c64。FULL_DECODE_ONLY、force EPLB 等保持脚本声明；未冒充缺失的 resolved 日志。

| Case | 源 MiB | Client c | 实际 prompt tokens | Profiled token TPOT P50 ms |
|---|---:|---:|---|---:|
| deepseek_v4_1_flash_fp8_high_conc_decode_c4_p2k | 95.72 | 4 | [2048] | 16.5619 |
| deepseek_v4_1_flash_fp8_high_conc_decode_c16_p2k | 82.08 | 16 | [2048] | 20.6166 |
| deepseek_v4_1_flash_fp8_high_conc_decode_c32_p2k | 66.92 | 32 | [2048] | 22.3930 |
| kimi_k3_tp8_high_conc_decode_c1_p16k | 97.46 | 1 | [16392] | 35.8135 |
| kimi_k3_tp8_high_conc_decode_c2_p16k | 96.73 | 2 | [16392] | 41.4175 |
| kimi_k3_tp8_high_conc_decode_c4_p16k | 93.19 | 4 | [16392] | 49.4462 |
| kimi_k3_tp8_high_conc_decode_c8_p16k | 87.98 | 8 | [16392] | 65.3152 |
| kimi_k3_tp8_high_conc_decode_c16_p16k | 81.32 | 16 | [16392] | 100.2188 |
| kimi_k3_tp8_high_conc_decode_c32_p16k | 71.19 | 32 | [16392] | 164.7410 |
| glm5_3_flash_w8a8_high_conc_decode_aclgraph_c8 | 63.78 | 8 | [4096] | 60.2748 |
| glm5_3_flash_w8a8_high_conc_decode_aclgraph_c16 | 66.76 | 16 | [4096] | 70.2419 |
| glm5_3_flash_w8a8_high_conc_decode_aclgraph_c32 | 68.42 | 32 | [4096] | 92.2112 |
| glm5_3_flash_w8a8_high_conc_decode_aclgraph_c64 | 80.25 | 64 | [4096] | 301.6432 |

以上均为客户端指标与源制品身份；Body、层耗时和实际每步 B/q/context 仍由后续结构引导提取产生。来源相同的不同运行时预测不增加实测分母。
