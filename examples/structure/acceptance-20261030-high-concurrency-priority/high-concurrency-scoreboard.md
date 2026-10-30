## 已接受的 source arms

13 个独立来源 / 877 次选中 Body Forward。两个表格有交集，分母只计一次。接受建模声明不代表精度达标。

| Case / source family | 当前保留结果 | 最近执行 | Body error | calibration / evaluation | 契约边界 | 当前 runtime / receipt |
|---|---|---|---:|---|---|---|
| qwen36-a5-tp2-c96 / qwen36_tp2_hccl | Body PASS | COMPLETED | -1.59% | in_sample / in_sample | Body 不证明 native strict 闭合 | `e71d76a0e8fb` / [3132121ac920](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-service-replay.json) |
| qwen35-35b-a5-tp4-c128-graph / qwen35_mc2_tp | Body PASS | COMPLETED | -13.56% | observed / in_sample | Body 不证明 native strict 闭合 | `c347250c5f5e` / [c904ff473d19](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-complete-observed-service/decode-forward-complete-service-replay.json) |
| qwen35-35b-a5-tp4-c4-graph / qwen35_mc2_tp | Body PASS | COMPLETED | -14.66% | observed / in_sample | Body 不证明 native strict 闭合 | `c347250c5f5e` / [a8eb0e4b6ec6](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-complete-observed-service/decode-forward-c4-gdn-helpers-replay.json) |
| qwen35-35b-a5-tp4-c64-graph / qwen35_mc2_tp | Body PASS | COMPLETED | -14.28% | observed / in_sample | Body 不证明 native strict 闭合 | `c347250c5f5e` / [c904ff473d19](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-qwen35-complete-observed-service/decode-forward-complete-service-replay.json) |
| qwen36-a5-tp2-c12 / qwen36_tp2_hccl | Body PASS | COMPLETED | -11.33% | observed / in_sample | Body 不证明 native strict 闭合 | `57520ed725bf` / [3c8fea138325](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-cohort-service-replay.json) |
| qwen36-a5-tp2-c1 / qwen36_tp2_hccl | Body PASS | COMPLETED | -12.98% | observed / in_sample | Body 不证明 native strict 闭合 | `57520ed725bf` / [3c8fea138325](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-cohort-service-replay.json) |
| v4flash-a3-tp8-c4 / v4_a3_caller_bf16 | Body PASS | COMPLETED | -14.92% | not_declared / not_declared | Body 不证明 native strict 闭合 | `1c7fc78cb8be` / [c29b9ee49edb](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-a3-v4-caller-cc245da6/decode-forward-a3-v4-caller-replay.json) |
| v4flash-a3-tp8-c8 / v4_a3_caller_bf16 | Body PASS | COMPLETED | -8.09% | not_declared / not_declared | Body 不证明 native strict 闭合 | `1c7fc78cb8be` / [c29b9ee49edb](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-a3-v4-caller-cc245da6/decode-forward-a3-v4-caller-replay.json) |

## 六个 A5 高并发重点

| Case | Real Mean / P50 / P90 ms | Sim ms / error | Delta / 到 15% 带 ms | 客户端 TPOT Mean / P50 / P90 ms | 场景目标 / 文件名标签 | 最近执行 runtime / receipt |
|---|---:|---:|---:|---|---|---|
| qwen36-a5-tp2-c96 (Body PASS; latest COMPLETED) | 63.853 / 63.562 / 65.419 | 62.838 / -1.59% | -1.015 / 0.000 | 31.634 / 31.824 / 35.239 | tpot30ms / tpot30ms（仅标签） | `e71d76a0e8fb` / [3132121ac920](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-service-replay.json) |
| a5_kimi_tp8_e16_bf16_c32_p4k (Body PASS; latest COMPLETED) | 40.019 / 40.018 / 40.044 | 36.969 / -7.62% | -3.050 / 0.000 | — / 69.663 / — | 未声明 / 无（仅标签） | `57520ed725bf` / [bf57fac3d529](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-composed-service/decode-forward-composed-replay.json) |
| a5_kimi_tp8_e16_bf16_c32_p16k (Body PASS; latest COMPLETED) | 44.666 / 44.645 / 44.662 | 42.156 / -5.62% | -2.511 / 0.000 | — / 164.741 / — | 未声明 / 无（仅标签） | `57520ed725bf` / [bf57fac3d529](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-kimi-composed-service/decode-forward-composed-replay.json) |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 (Body PASS; latest COMPLETED) | 26.328 / 26.306 / 26.336 | 24.812 / -5.76% | -1.517 / 0.000 | 29.265 / 28.943 / 30.069 | 未声明 / tpot30ms（仅标签） | `e71d76a0e8fb` / [50e8c2d4b89e](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-replay.json) |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k (Body PASS; latest COMPLETED) | 27.286 / 27.266 / 27.290 | 25.540 / -6.40% | -1.746 / 0.000 | — / 33.341 / — | 未声明 / 无（仅标签） | `e71d76a0e8fb` / [50e8c2d4b89e](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-replay.json) |
| a5_glm53flash_tp8_c64_p4k (Body PASS; latest COMPLETED) | 46.528 / 46.499 / 46.645 | 47.971 / 3.10% | 1.443 / 0.000 | — / 29.828 / — | 未声明 / 无（仅标签） | `13100107089f` / [4726afd58be0](/Volumes/data/code/mindie-release-20261014/profiler/examples/structure/acceptance-20261030-service-glm/metadata-pass/decode-forward-service-replay.json) |

Delta = Sim − Real；“到 15% 带”是统计验收超额，不是待补物理服务预算。客户端 TPOT、场景目标和 Body Forward 是不同指标。最新执行失败时，旧的成功结果可以保留，但不能冒称最新执行已完成。
