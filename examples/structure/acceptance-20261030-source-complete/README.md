# 同一 Sim 版本的 66 源 Decode 回放

复用已有采集和已验收 Body 边界，不是新一轮真机采集。固定 Sim 提交为 `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`。每个输入保存采集、提取结果及模型声明的 SHA；没有根据误差挑选条件臂。

| 输入组 | 完成预测的来源 | Body ≤15% |
|---|---:|---:|
| GLM：18 Flash + 8 完整模型 | 26 | 12 |
| A5 Kimi TP8，4K/16K × 6 并发 | 12 | 0 |
| A5 V4.1 dynamic + rotary | 7 | 0 |
| A5 Qwen TP4/TP2 source GDN | 6 | 0 |
| 保持原声明的其余来源 | 15 | 10 |
| 合计 | 66 | 22 |

66 个主桶均完成，无失败或超时，覆盖 4,662 次实测 Forward。全部 222 个实测几何群、5,250 次 Forward 仍保留；另外 156 个几何群没有在本轮逐一预测。单个预测进程最高 462.625 MiB，最长 46.221 秒，预算仍是 512 MiB / 90 秒。

Kimi 使用 `kimi-source-complete`（实际代表 context、stateful convolution）；A5 GLM 使用 `glm-source-complete`（accepted-state KDA 与真正的融合 gate-up 资源程序），A3 Flash 使用 `glm-source-accepted-26`，完整 GLM 保留原有 RoPE/KV 边界；Qwen 使用 `qwen-source-gdn-native`。这些显式源条件不等于已证明私有二进制的全部运行参数。

[版本对比](body-runtime-delta.md) 保留旧失败收据，确认两项新增 PASS、没有丢失原 PASS。Kimi 的 12 个 dispatch 失败已修复，但 Body 精度仍未达标。重算脚本、来源分母和逐层结果保存在五组 `decode-forward-*-cases.json` / `decode-forward-*-replay.json` 中；调用 `replay_decode_forwards.py` 时使用固定 checkout、`--geometry-limit 1`、`--prediction-timeout 90` 和上述 `--runtime-source-commit`。

[统一三层记分牌](../acceptance-20261030-priority/priority-three-level-scoreboard.md) 单独统计严格算子对账与条件源参考。算子活动残差不能直接相加解释 Body 墙钟差额。Qwen 的完整剩余账见[算子及通信残差](../acceptance-20261030-qwen-source-native-operators/runtime30dcea1e/qwen-body-operator-residual-ledger.md)；GLM 见[直接契约与条件源参考](../acceptance-20261030-glm-source-complete-operators/glm-source-complete-residuals.md)。

V4.1 七源的[完整原生算子参考](../acceptance-20261030-v41-native-references-30dcea1e-bounded/v41-native-reference-scoreboard.json) 覆盖 830 Forward、182,600 次调用（每次 Forward 220 次），均为条件源参考。工具提前释放已校验的实际算子表和模型副本，将 c128 结构导出及参考计算峰值降到 489.08 MiB；完整 DP/层结构和成本不变，旧失败及 c16 已成功成本的原始身份均保留。
