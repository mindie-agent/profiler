# V4.1 后续 6 源

A3 五源为 TP4/DP4/EP16、DSpark7、Engram 禁用、fused MC2 的独立部署；A5 c128 沿用 TP1/DP8/EP8、Engram 开启且无 MTP。不得共享同一执行配方。

A3 每源 16 rank 保留；选择 dp0_tp0，解压 SHA 与顶层 CSV 完全相同。其他 rank 未做事件扫描。FULL_DECODE_ONLY、force EPLB 等 A3 条件目前是启动脚本声明，未冒充 resolved 日志。

| Case | MiB | Profiled client c | Prompt tokens | Token TPOT P50 ms |
|---|---:|---:|---|---:|
| deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c4 | 58.30 | 4 | [4096] | 56.226793 |
| deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c8 | 59.67 | 8 | [4096] | 57.909682 |
| deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c16 | 60.82 | 16 | [4096] | 58.612550 |
| deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c32 | 61.14 | 32 | [4096] | 64.090632 |
| deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c64 | 61.49 | 64 | [4096] | 81.775784 |
| deepseek_v4_1_flash_fp8_high_conc_decode_c128_p2k | 47.03 | 128 | [2048] | 33.341304 |

该表为客户端指标，不是主体 Forward 耗时；实测 q/B、结构完整性和 body/activity 由后续解析给出。
