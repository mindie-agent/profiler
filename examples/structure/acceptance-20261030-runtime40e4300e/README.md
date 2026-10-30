# 40e4300e 完整 Body 与源码组合回放

固定 Sim `40e4300ea7ccc1123759f6201cc2d69e3aa77ad6`，package SHA `ab51c56356b3b6f11a130dd7a59d2fd894b99148d0917fc4cc40189102286124`。66 个来源全部完成基线预测，22/66 达标；加上 3 个 Qwen HCCL、10 个 GLM 源码组合和 10 个 HBM-only 控制，另有 10 个修正 shared/routed 合并后归约的 GLM 案例，共 99 个完成对比臂。条件臂不增加独立采集来源数。

沿用 5,250 个完整 Forward、222 个几何人口。控制核别名修复后，最终 8 份 `*-controller-replay.json` 全部复用同输入预测缓存，没有重新计算成本。独立数值复核 22,795 项通过。预测 worker 峰值 430.23 MiB，最大成功耗时 74.54s；父级汇总内存与 worker 分开记录。

| 组 | 来源/对比臂 | 达标 | 最终执行失败 |
|---|---:|---:|---:|
| glm | 26 | 12 | 0 |
| kimi | 12 | 0 | 0 |
| qwen | 6 | 0 | 0 |
| v41 | 7 | 0 | 0 |
| remaining | 15 | 10 | 0 |
| qwen-hccl | 3 | 0 | 0 |
| glm-hbm-control | 10 | 1 | 0 |
| glm-source-composed | 10 | 1 | 0 |
| glm-join-reduce (final) | 10 | 1 | 0 |

最新观测入口是 [controller generation map](../acceptance-20261030-controller-alias/extraction-generation-map.json)。原始 `*-replay.json` 保留运行时变更和失败恢复证据；主板采用 `*-controller-replay.json` 的更新层统计。所有 Body 起止、层起点和算子人口均保持；仅控制记录产生的 union/层末端按真实 successor 修正。

源码案例来自 Sim 已提交的 `ac22f6f5`（Qwen HCCL）和 `a86a6d09`（GLM 两臂），manifest 中有逐文件 SHA 与原始提交。只复制案例到固定 runtime 的 `examples/`；没有更新运行时代码或硬件速率。完整 V4.1 composed 案例保留原先显式 DP8 对称声明。

Qwen TP2 c96 的 53.947 ms 对比实测 63.853 ms，−15.51%，仍未通过。GLM 两个 10 案例组均只有 c96 通过；源码服务率只是显式启发式条件，不能视为已捕获的模板或实测速率。

两项执行问题均保留：B1/q1 元数据物理图错误由 `f0d89c6` 修复；V4.1 c128 初次 90s 超时后，在相同输入、相同预算下降低队列并发重试，74.54s 完成。旧失败未冒充成功。

复现任意最终报告（替换 `glm` 选择组）：

```sh
PYTHONPATH=/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029:/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-glm-controller-cases.json \
  --output /tmp/decode-forward-glm-controller-replay.json --geometry-limit 1 \
  --prediction-timeout 90 --runtime-source-commit 40e4300ea7ccc1123759f6201cc2d69e3aa77ad6
```

本轮均为既有硬件采集的离线回放，无新真机任务。全量本地测试 793 passed / 26 skipped；新增主板 supplement、controller overlay 的定向测试另见相应独审与提交。

GLM 最终推荐臂来自 `f57540a8`：shared/routed add 后仅一次 TP 归约，90 = 45 attention + 45 FFN；移除额外 42 个专家归约，非通信工作保持。十例全部完成，c96 为 59.368 ms / +3.09% PASS，其余仍有 −25.81% 至 −56.45% 的低估。主板选择 [join-reduce 回放](decode-forward-glm-join-reduce-replay.md)，旧两臂保留为历史条件；[逐例差异](glm-join-reduce-delta.md) 不把残差抵消当作精度。

V4.1 新代严格分母排除了 14 个物理资源边界已经变化的旧 HcPost cohort（仍保留条件参考），并新增 3 个未达标的 routing cohort，因此微算子统计由 753/773 变为 739/762；这不是删除失败来提升通过率。
