# 高并发重点来源与当前 source arm

当前主板 SHA `095db1739b4e9edeadfd3a2f779a17a72c49d67c798bc327c21fb0c3a6b26241`；13 个独立来源，六个高并发重点与八个显式 source-family case 有一个重叠。零原始采集扫描、零成本重算。

| Case | q / B | Body Mean / P50 / P90 ms | Sim ms / error | Body PASS | strict cohort pass/compared | refs | client TPOT / target |
|---|---|---:|---:|---|---:|---:|---|
| qwen36-a5-tp2-c96 | 4 / 96 | 63.853 / 63.562 / 65.419 | 53.947 / -15.51% | False | 8/13 | 6 | mean 31.634 ms; P50 31.824 ms; P90 35.239 ms; target tpot30ms |
| a5_kimi_tp8_e16_bf16_c32_p4k | 1 / 32 | 40.019 / 40.018 / 40.044 | 28.544 / -28.67% | False | 11/11 | 36 | P50 69.663 ms; target not explicitly retained |
| a5_kimi_tp8_e16_bf16_c32_p16k | 1 / 32 | 44.666 / 44.645 / 44.662 | 33.731 / -24.48% | False | 11/11 | 36 | P50 164.741 ms; target not explicitly retained |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 1 / 8 | 26.328 / 26.306 / 26.336 | 18.933 / -28.09% | False | 16/16 | 25 | mean 29.265 ms; P50 28.943 ms; P90 30.069 ms; target capture label tpot30ms only |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 1 / 16 | 27.286 / 27.266 / 27.290 | 19.245 / -29.47% | False | 16/16 | 25 | P50 33.341 ms; target not explicitly retained |
| a5_glm53flash_tp8_c64_p4k | 4 / 64 | 46.528 / 46.499 / 46.645 | 34.519 / -25.81% | False | 19/20 | 5 | P50 29.828 ms; target not explicitly retained |
| qwen35-35b-a5-tp4-c128-graph | 4 / 128 | 28.585 / 28.571 / 28.704 | 16.622 / -41.85% | False | 13/13 | 20 | mean 15.922 ms; P50 15.843 ms; P90 18.469 ms; target capture label tpot30ms only |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | 11.551 / 11.482 / 11.818 | 4.706 / -59.26% | False | 12/12 | 20 | mean 7.155 ms; P50 7.133 ms; P90 7.623 ms; target capture label tpot5ms only |
| qwen35-35b-a5-tp4-c64-graph | 4 / 64 | 21.957 / 22.001 / 22.068 | 11.723 / -46.61% | False | 12/12 | 20 | mean 12.604 ms; P50 12.0 ms; P90 14.398 ms; target capture label tpot10ms only |
| qwen36-a5-tp2-c12 | 4 / 12 | 24.226 / 24.053 / 24.711 | 18.850 / -22.19% | False | 13/13 | 6 | mean 12.738 ms; P50 12.657 ms; P90 13.223 ms; target tpot10ms |
| qwen36-a5-tp2-c1 | 4 / 1 | 12.318 / 12.279 / 12.362 | 7.726 / -37.28% | False | 13/13 | 6 | mean 8.043 ms; P50 8.043 ms; P90 8.043 ms; target tpot5ms |
| v4flash-a3-tp8-c4 | 2 / 4 | 32.486 / 32.416 / 32.734 | 27.638 / -14.92% | True | 0/0 | 0 | mean 53.936 ms; P50 47.929 ms; P90 73.738 ms; target 30 |
| v4flash-a3-tp8-c8 | 2 / 8 | 37.763 / 37.868 / 38.082 | 34.707 / -8.09% | True | 0/0 | 0 | mean 68.12 ms; P50 62.964 ms; P90 95.11 ms; target 50 |

建议直接展示已选中的 source arm，并保留旧臂历史。执行成功、Body ±15% 精度、strict native-contract 覆盖和条件参考必须分别标注。TPOT 的客户端/目标口径不可替代 Body Forward；reference 数不与 strict 分母相加。
