# Kimi source 配方：17 源完整算子族回放

固定 Sim `18c423c7297fc3b3e92a5eb34f204df40a2a6cb6`，使用 `kimi-source/*_source.json` 的显式配置重新导出结构和物理工作量。A5 12 源复用 logical96 已完整重绑的 MatMul 观测；A3 5 源保留其四层 W4A8 观测。所有源均使用原先完整 Body 的主几何，合计 1,769 次 Forward；不是额外采集。

[完整报告](body-operator-family-scoreboard.json) 保留全部算子族和原观测直方图，包含 177 个严格 cohort、172 个通过：`<=50 us` 为 167/167，`>50 us` 为 5/10。严格事件 349,095；没有 strict 重绑排除或成本失败。34 组旧 native 参考可重新绑定，24 组因显式 MC2 结构变化保留排除记录；这些排除不算严格失败或零耗时。

本轮 17 源均运行新成本，耗时 162.78 秒；没有读取原始 CSV，没有复用旧预测。实际输入与覆盖变化逐源保存在 `source_case_overrides`、`declaration_refresh` 和子目录成本回执。source 配方选择不会把 routed buffer capacity 变成有效工作量，也不证明对端到达时间。

[独立算术审核](body-operator-reprice-independent-review.json) 通过 10,270 项检查。审核逐源核对 actual、mapping、case、comparison 的内容身份，完整直方图、全族人口守恒以及两档精度算术。

六类完整原生 ABI 的新增条件参考另见 [Kimi native reference 报告](../acceptance-20261030-kimi-source-references/README.md)。它们不覆盖这里的 canonical 全族报告，也不增加这里的 strict 分母。
