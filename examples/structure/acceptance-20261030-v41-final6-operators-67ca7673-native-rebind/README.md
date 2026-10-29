# V4.1 final6（五 A3 + 一 A5）：runtime67 零 raw 重估

固定 Sim commit `67ca76738c3d6acaa44d8258cc4ba9b5534e1cbf`。复用已验收的完整 target-body 实测分桶与直方图，重新导出结构、验证 source/geometry/contract/候选集合并计算新成本；随后只重试条件 reference，全部 strict comparison 文件 SHA 原样保留。没有读取原始 CSV，也没有启用正式 case 未声明的 source MXA8W4 长 K 条件。

最终状态 `completed`，覆盖状态 `partial`。独立 3,697 项检查通过；63/63 strict cohorts、77,355 strict events，全部属于 ≤50us/绝对误差15us档。不能由这些通过率推出重型算子或整模型误差已通过。保留 10 个条件参考，另有 4 个因物理程序已变、尚未完成完整 source/ABI 重绑定而排除。实测事件仍保留在总分母中。

| Case | 选中完整 body | B / Q / M | Strict pass/compared | Reference groups | Excluded reference groups |
| --- | ---: | --- | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 32 | 5 / 8 / 40 | 9/9 | 1 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 22 | 9 / 8 / 72 | 9/9 | 1 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 48 | 2 / 8 / 16 | 9/9 | 1 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 21 | 17 / 8 / 136 | 9/9 | 1 | 0 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 29 | 4 / 8 / 32 | 9/9 | 1 | 0 |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 73 | 16 / 1 / 16 | 18/18 | 5 | 4 |

Reference 不进入 strict 达标分母。A5 保留的五组是三个物理不同的 MQS attention 子组及 attention/FFN 的 HcPre partial-base 分组；GroupedMatmul up/down、DispatchV3、CombineV3 四组未沿用旧 physical work，仍明确排除。它们存在完整 native ABI，但本轮新增的重绑定能力仅覆盖 A3 DispatchFFNCombine，不能静默将这四类旧参考恢复。

## 执行与失败链

初轮新成本耗时 214.135s，所有 strict programs 成功。初轮 A5 references 因重复存活的 manifest/graphs 触发 `comparison_worker_exceeds_512_mib`，初轮报告保留 `status=partial`、原始 stderr 和 failed receipt，见 [初轮报告](../acceptance-20261030-v41-final6-operators-67ca7673/body-operator-family-scoreboard.json)。工具修复只释放不再使用的结构对象，不更改成本算法。

本最终轮耗时 27.096s，new_strict_program_count=0；reference attempt history、previous receipts、strict source report SHA 与新 helper/tool identity 分列。各次 source/case/mapping/Sim 文件 hash 经过验证。旧六 validate-only 曾观测进程 RSS 528.0 MiB（`ps` 单点，非精确峰值），该超目标记录不隐去；修复后的 reference 执行均低于 512 MiB。

A5 c128 先做一次内存修复 trial（8.89s，500.0 MiB），记录在 [refs-retry](../acceptance-20261030-v41-final6-operators-67ca7673-refs-retry/body-operator-family-scoreboard.json)；最终轮复用该成功 reference，仅重算五 A3 MC2。

## MC2 完整 ABI 重绑定

原始 SourceRoleReferences 分桶 key 包含完整 8 输入/2 输出 native ABI，而不只是两个 examples。每个保存的 layer_id 都重新经过同一 source selector，验证 dtype/layout/专家权重轴/top-k 与全部九个 routed roles；只在所有层物理程序仍同构时保留整组直方图。任一层改变会拒绝拆分旧 aggregate。原始 histogram、body 范围、source identity、mask/有效 routed rows 的 unknown 状态均保留，source reference 仍非 strict tensor cohort。

| Case | MC2 observed ms/F | Decomposed reference ms/F | Difference ms/F |
| --- | ---: | ---: | ---: |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 27.939907 | 36.997245 | +9.057338 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 28.721821 | 37.626821 | +8.905000 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 28.483128 | 36.632751 | +8.149623 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 28.737108 | 38.907964 | +10.170856 |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 27.760711 | 36.874932 | +9.114221 |

这些条件参考与旧九程序 decomposition 的数值相同，恢复的是完整证据到新声明的关联，不是原子 MC2 cost 收敛。native fusion 的 launch/HBM 消除、MC2 排程和 valid-mask 实际值仍未证实；不能将这些 kernel activity 差值当成可加总的 body wall-clock 因果预算。

五个 A3 case 的 strict cohorts 均为9/9，前一代 c4/c32/c64 的 compress_gates/compress_values 微秒档失败已修复；A5 c128 为18/18。

[最终记分牌](body-operator-family-scoreboard.md) · [机器结果](body-operator-family-scoreboard.json) · [独立审查](body-operator-reprice-independent-review.json)。最终 JSON SHA256：`9f7de958613c79fac0d03def2d6bfd1477425ed5335c5d30fd55b9e940ce88e9`。
