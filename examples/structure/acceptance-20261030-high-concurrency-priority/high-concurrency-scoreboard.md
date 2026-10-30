## 已接受的 source arms

13 个独立来源 / 877 次选中 Body Forward。两个表格有交集，分母只计一次。接受建模声明不代表精度达标。

| Case / source family | 当前保留结果 | 最近执行 | Body error | calibration / evaluation | 契约边界 | 当前 runtime / receipt |
|---|---|---|---:|---|---|---|
| qwen36-a5-tp2-c96 / qwen36_tp2_hccl | Body FAIL | COMPLETED | -15.51% | not_declared / not_declared | Body 不证明 native strict 闭合 | `ab51c56356b3` / [ba463c3f20c6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-qwen-hccl-controller-replay.json) |
| qwen35-35b-a5-tp4-c128-graph / qwen35_mc2_tp | Body FAIL | COMPLETED | -41.85% | not_declared / not_declared | Body 不证明 native strict 闭合 | `db3e8eafccff` / [2f99d9fa09b6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-mc2-tp-bf71bd7d/decode-forward-qwen35-mc2-tp-replay.json) |
| qwen35-35b-a5-tp4-c4-graph / qwen35_mc2_tp | Body FAIL | COMPLETED | -59.26% | not_declared / not_declared | Body 不证明 native strict 闭合 | `db3e8eafccff` / [2f99d9fa09b6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-mc2-tp-bf71bd7d/decode-forward-qwen35-mc2-tp-replay.json) |
| qwen35-35b-a5-tp4-c64-graph / qwen35_mc2_tp | Body FAIL | COMPLETED | -46.61% | not_declared / not_declared | Body 不证明 native strict 闭合 | `db3e8eafccff` / [2f99d9fa09b6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-mc2-tp-bf71bd7d/decode-forward-qwen35-mc2-tp-replay.json) |
| qwen36-a5-tp2-c12 / qwen36_tp2_hccl | Body FAIL | COMPLETED | -22.19% | not_declared / not_declared | Body 不证明 native strict 闭合 | `ab51c56356b3` / [ba463c3f20c6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-qwen-hccl-controller-replay.json) |
| qwen36-a5-tp2-c1 / qwen36_tp2_hccl | Body FAIL | COMPLETED | -37.28% | not_declared / not_declared | Body 不证明 native strict 闭合 | `ab51c56356b3` / [ba463c3f20c6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-qwen-hccl-controller-replay.json) |
| v4flash-a3-tp8-c4 / v4_a3_caller_bf16 | Body PASS | COMPLETED | -14.92% | not_declared / not_declared | Body 不证明 native strict 闭合 | `1c7fc78cb8be` / [c29b9ee49edb](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-a3-v4-caller-cc245da6/decode-forward-a3-v4-caller-replay.json) |
| v4flash-a3-tp8-c8 / v4_a3_caller_bf16 | Body PASS | COMPLETED | -8.09% | not_declared / not_declared | Body 不证明 native strict 闭合 | `1c7fc78cb8be` / [c29b9ee49edb](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-a3-v4-caller-cc245da6/decode-forward-a3-v4-caller-replay.json) |

## 六个 A5 高并发重点

| Case | Real Mean / P50 / P90 ms | Sim ms / error | Delta / 到 15% 带 ms | 客户端 TPOT Mean / P50 / P90 ms | 场景目标 / 文件名标签 | 最近执行 runtime / receipt |
|---|---:|---:|---:|---|---|---|
| qwen36-a5-tp2-c96 (Body FAIL; latest COMPLETED) | 63.853 / 63.562 / 65.419 | 53.947 / -15.51% | -9.906 / 0.328 | 31.634 / 31.824 / 35.239 | tpot30ms / tpot30ms（仅标签） | `ab51c56356b3` / [ba463c3f20c6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-qwen-hccl-controller-replay.json) |
| a5_kimi_tp8_e16_bf16_c32_p4k (Body FAIL; latest COMPLETED) | 40.019 / 40.018 / 40.044 | 28.544 / -28.67% | -11.475 / 5.472 | — / 69.663 / — | 未声明 / 无（仅标签） | `1c7fc78cb8be` / [e0bda7ee4900](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency-priority/decode-forward-highconc-mc2-replay.json) |
| a5_kimi_tp8_e16_bf16_c32_p16k (Body FAIL; latest COMPLETED) | 44.666 / 44.645 / 44.662 | 33.731 / -24.48% | -10.936 / 4.236 | — / 164.741 / — | 未声明 / 无（仅标签） | `1c7fc78cb8be` / [e0bda7ee4900](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency-priority/decode-forward-highconc-mc2-replay.json) |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 (Body FAIL; latest COMPLETED) | 26.328 / 26.306 / 26.336 | 18.933 / -28.09% | -7.396 / 3.446 | 29.265 / 28.943 / 30.069 | 未声明 / tpot30ms（仅标签） | `1c7fc78cb8be` / [e0bda7ee4900](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency-priority/decode-forward-highconc-mc2-replay.json) |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k (Body FAIL; latest COMPLETED) | 27.286 / 27.266 / 27.290 | 19.245 / -29.47% | -8.041 / 3.948 | — / 33.341 / — | 未声明 / 无（仅标签） | `1c7fc78cb8be` / [e0bda7ee4900](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-high-concurrency-priority/decode-forward-highconc-mc2-replay.json) |
| a5_glm53flash_tp8_c64_p4k (Body FAIL; latest COMPLETED) | 46.528 / 46.499 / 46.645 | 34.519 / -25.81% | -12.009 / 5.030 | — / 29.828 / — | 未声明 / 无（仅标签） | `ab51c56356b3` / [25e6ecbf8c40](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-glm-join-reduce-replay.json) |

Delta = Sim − Real；“到 15% 带”是统计验收超额，不是待补物理服务预算。客户端 TPOT、场景目标和 Body Forward 是不同指标。最新执行失败时，旧的成功结果可以保留，但不能冒称最新执行已完成。
