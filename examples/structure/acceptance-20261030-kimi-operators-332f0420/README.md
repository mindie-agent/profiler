# Kimi 正确量化与 Window-8 主体算子回放

本批复用 17 份 A3/A5 采集中的 1,799 个已验收 Decode 主体；选择每源最大几何桶，共 1,769 个主体（98.33%），其余 30 个主体仍保留在完整覆盖分母中。每源独立流式扫描和成本计算，没有启动新设备采集。

使用修复 HF wrapper 外层量化覆盖的 Sim `332f0420` 成本实现，以及显式 finite peer window-8 声明。A5 使用 BF16，A3 四层模型使用 W4A8。运行期间 Sim/profiler 成本和解析源文件指纹保持不变。旧 `09811dad` Kimi 预测因量化输入未生效而失效，见[统一失效旁注](../acceptance-20261030-kimi-variants/prediction-input-binding-invalidation.json)；本批没有复用旧错误成本。

## 覆盖和精度必须一起看

严格契约对账覆盖 **285,375 / 3,545,622 个主体内事件（8.05%）**。其余事件仍完整出现在全族表中，按条件参考或未解析原因列出，不能算作零成本、通过或 Sim 漏算。

| 严格计分口径 | 通过 / 对比 |
|---|---:|
| 单次实测 ≤ 50 us，绝对误差 ≤ 15 us | 149 / 149 |
| 单次实测 > 50 us，相对误差 ≤ 15% | 5 / 10 |
| 合计 | 154 / 159 |

154/159 是已覆盖算子 cohort 的通过数，不能解释为整模型通过率。同期完整主体比较仍是 **1/17 通过、12/1,136 层通过**，见[主体回放](../acceptance-20261030-kimi-variants/decode-forward-332f0420-window8-replay.md)。严格算子计分中的五个失败均为 A3 dense FFN `QuantBatchMatmulV3 / gate_up`，实测约 54.6–60.6 us，预测约 72.3–89.3 us。

## 头部活动与后续定位

- A5 c16 / 4K：专家上投影约 4.045 ms/Forward，派发 3.074 ms，AttnRes 2.093 ms，专家下投影 1.962 ms。专家矩阵和通信目前是条件参考，AttnRes 尚未形成严格 tensor cohort。
- A3 c64：专家上/下投影分别约 3.287 / 1.562 ms/Forward，RecurrentKda 约 0.530 ms，MLA FIA 约 0.506 ms。
- 上述是事件区间时长之和，真实通信中的对端等待也包含在内，并可能跨 stream 重叠；不能相加替代主体跨度，也不能用于反推链路带宽。
- 条件 source-role program 只引用已有 Sim 工作量，不额外增加成本预算，不证明 Host occurrence 绑定。特别是 FIA 单个 program 参考不能冒充整个 batch 的精确执行成本。

## 制品

- [完整算子族表](body-operator-family-scoreboard.md)：每源全部已观测家族、严格误差和未计分原因。
- [KDA / MLA / FFN 活动贡献](body-operator-structure-contributions.md)：按各结构区域的实测 ms/Forward 排序。
- [机器可读结果](body-operator-family-scoreboard.json)：保留所有事件分母、契约候选、条件参考和源身份。
- [稳态层精确调用池](steady-layer-pooled.json)：仅排除 Layer 0 的 60,309 个完整层调用；未从完整主体中删减 Layer 0。
- [独立算术审核](body-operator-family-independent-review.json)：9,315 项检查通过，无原始采集重读或新预测。
- [独立来源与有效量化审核](body-operator-source-independent-review.json)：3,566 项检查通过；逐源流式审核 RSS 172 MiB，并如实保留首轮整读审核超出预算后被替换的记录。

各源子目录保留实际事件摘要、结构映射、声明、成本回执、精确时长直方图和执行日志。全局 JSON 小于 32 MiB；原始 CSV 未复制入库。

复跑入口是 `examples/structure/replay_body_operator_queue.py`，输入声明为 `../acceptance-20261030-kimi-variants/decode-forward-quant-fixed-window8-cases.json`，主体接受回执为同目录的 `decode-forward-auto-acceptance.json`。必须选择与本批身份一致的 Sim 代码和量化声明；修改成本或声明后应另存新变体，不能覆盖本批来源。
