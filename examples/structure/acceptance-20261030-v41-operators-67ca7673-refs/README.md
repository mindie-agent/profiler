# V4.1 旧六 A5：runtime67 零 raw 重估

固定 Sim commit `67ca76738c3d6acaa44d8258cc4ba9b5534e1cbf`。复用已验收的完整 target-body 实测分桶与直方图，重新导出结构、验证 source/geometry/contract/候选集合并计算新成本；随后只重试条件 reference，全部 strict comparison 文件 SHA 原样保留。没有读取原始 CSV，也没有启用正式 case 未声明的 source MXA8W4 长 K 条件。

最终状态 `completed`，覆盖状态 `partial`。独立 5,297 项检查通过；108/108 strict cohorts、444,359 strict events，全部属于 ≤50us/绝对误差15us档。不能由这些通过率推出重型算子或整模型误差已通过。保留 30 个条件参考，另有 24 个因物理程序已变、尚未完成完整 source/ABI 重绑定而排除。实测事件仍保留在总分母中。

| Case | 选中完整 body | B / Q / M | Strict pass/compared | Reference groups | Excluded reference groups |
| --- | ---: | --- | ---: | ---: | ---: |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | 129 | 2 / 1 / 2 | 18/18 | 5 | 4 |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | 105 | 4 / 1 / 4 | 18/18 | 5 | 4 |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | 151 | 1 / 1 / 1 | 18/18 | 5 | 4 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 145 | 1 / 1 / 1 | 18/18 | 5 | 4 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 75 | 8 / 1 / 8 | 18/18 | 5 | 4 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 152 | 1 / 1 / 1 | 18/18 | 5 | 4 |

Reference 不进入 strict 达标分母。A5 保留的五组是三个物理不同的 MQS attention 子组及 attention/FFN 的 HcPre partial-base 分组；GroupedMatmul up/down、DispatchV3、CombineV3 四组未沿用旧 physical work，仍明确排除。它们存在完整 native ABI，但本轮新增的重绑定能力仅覆盖 A3 DispatchFFNCombine，不能静默将这四类旧参考恢复。

## 执行与失败链

初轮新成本耗时 395.853s，所有 strict programs 成功。初轮 A5 references 因重复存活的 manifest/graphs 触发 `comparison_worker_exceeds_512_mib`，初轮报告保留 `status=partial`、原始 stderr 和 failed receipt，见 [初轮报告](../acceptance-20261030-v41-operators-67ca7673/body-operator-family-scoreboard.json)。工具修复只释放不再使用的结构对象，不更改成本算法。

本最终轮耗时 53.832s，new_strict_program_count=0；reference attempt history、previous receipts、strict source report SHA 与新 helper/tool identity 分列。各次 source/case/mapping/Sim 文件 hash 经过验证。旧六 validate-only 曾观测进程 RSS 528.0 MiB（`ps` 单点，非精确峰值），该超目标记录不隐去；修复后的 reference 执行均低于 512 MiB。

本轮六个 A5 reference worker 峰值 481.40625 MiB；初轮六个失败 attempt 均在每源历史中保留。Strict 108/108 与旧一代数量相同，所有实测直方图和候选集合在重绑定后保持一致。

[最终记分牌](body-operator-family-scoreboard.md) · [机器结果](body-operator-family-scoreboard.json) · [独立审查](body-operator-reprice-independent-review.json)。最终 JSON SHA256：`352ae526a827ec4ab5c9859057fbbc03bf01f655f4eb3f69ff0ddaaba537db7d`。
