# Kimi BF16：矩阵候选修复后的差值与结构缺口

本轮使用固定 Sim `86c1ee8f18b9b997eacb315476e2461b99b59fb1`，12 份 A5 TP8/EP8 BF16 采集的全部 618 个完整 Body 保持原实测边界。17 份 Kimi 算子成本重算还包括 5 份 A3 四层模型；下面的差值只统计这 12 份 A5，不混入 A3 或旧 DP4 的 p32k 采集。

新成本的独立审核为 9,910 项通过、0 失败。严格 cohort 仍为微秒档 149/149、大算子档 5/10；新增的 34 个完整原生 ABI 条件参考不进入这两个准确率分母。重算 158 个 worker，211.86 秒，最大 worker 210.30 MiB，无原始采集解析。

## 可计算差值的 Top 3

按 12 份采集的实际完整 Forward 数加权，下面是**算子活动差值**的前三项。它们不是 Body 墙钟误差的可加分解，也不是“超出容差”的排名；微秒算子即使累计活动差较大，单次仍可能处于 15 µs 容差内。

| 算子角色 | 证据层级 | 实测均值 µs/call | Sim µs/call | 少计活动 ms/Forward |
|---|---|---:|---:|---:|
| GroupedMatmul / expert_up | 完整 ABI 的条件源码参考 | 35.6148 | 22.3832 | 1.217306 |
| MatMulV3 / latent_down | 张量契约 + 整体拓扑条件角色 | 24.6853 | 14.1581 | 0.968498 |
| MatMulV3 / latent_up | 张量契约 + 整体拓扑条件角色 | 21.2322 | 14.1538 | 0.651216 |

三项各覆盖 56,856 次调用。GMM 的有效路由行数仍取自声明，原始 buffer capacity 不证明真实有效行或专家分布，所以它是条件参考。以 c32/p4k 为例，expert_up 实测 46.2374 µs、预测 23.8893 µs，单次相差 22.3481 µs；按 92 次/Forward 换算为 2.056025 ms 活动差。不能把它直接从 Body 误差中扣除。

独立诊断复核另有 4,969 项通过、0 失败，覆盖上述加权差值以及全部 204 个分区的 443,106 次矩阵直方图守恒，见 [审核回执](kimi-family-gap-independent-review.json)。

完整的每源结果、输入 SHA 和严格/条件两套排名见 [kimi-fixed-family-gap.json](kimi-fixed-family-gap.json) 与 [表格](kimi-fixed-family-gap.md)。原有严格 cohort 的 332f→67 成本基本不变，历史 Body 下降不能从这批严格矩阵的差值中推出。

## 同 runtime 的候选域隔离

[三臂对照](kimi-c32-matrix-domain-ablation.json) 在同一个源 case、同一个声明算子、同一精度和同一 `86c1ee8f` runtime 下，仅改变 `underfilled_candidates` / `narrow_candidates`：

| 声明程序 | 新默认 µs | 显式恢复 underfilled µs | 另恢复 narrow 的增量 µs |
|---|---:|---:|---:|
| linear_q | 17.576091 | 10.547728 | 0 |
| linear_decay_a | 17.570909 | 3.501684 | 0 |
| linear_beta | 4.814424 | 3.062485 | 0 |
| latent_down | 14.432865 | 14.432865 | 0 |
| latent_up | 14.302821 | 14.302821 | 0 |
| expert_up | 23.889253 | 23.889253 | 0 |

这些是声明程序的独立成本。采集中 KDA 前置投影实际为融合矩阵，因此不能把多个声明程序的差相加，当成该融合 kernel 或整模型的误差。Kimi 的 router 操作数和 compute 声明是 BF16；FP32 router 自动小 tile 的保留规则不能仅按 `router` 名称判断。

## 原有未评分矩阵已补齐完整证据

为解决每个 family 只有两个 ABI 示例的限制，本轮对 12 个原始本地 CSV 各做一次有界定向解析，只保留已验收的完整 Body 窗口内 MatMulV3。没有新采集、没有新增 Body，也没有改 Body 数字。

[解析回执](kimi-matrix-partition-receipt.json)：618 个 Body、443,106 次 MatMulV3、204 个完整 ABI × 层结构/区间/顺序分区；每源全部 MatMul 时长直方图与此前 actual 精确相同。总耗时 289.61 秒，单源峰值 198.08 MiB。每个分区保存全部时长分布、层/Forward 计数和原始定位。

这次发现的模型结构差异比继续调整矩阵速率更需要先解决：

- **KDA 融合前置投影**：c32/p4k 的 `[32,7168]→[32,6288]` 在 69 个 KDA 层各出现一次，共 3,174 次，活动 2.743509 ms/Forward。独立本地 upstream 源码 `vllm-verified-58d3918/.../nvidia/kda.py` 明确四路 Q/K/V/gate 各 1,536，加复制的 f_a 128 和 beta 12，再补齐到 16，得到 6,288。可以建立“兼容该源码”的融合子图条件映射；尚未证明采集容器与这份源码字节相同。
- **f_b 投影视图**：第二矩阵原始 ABI 是 flat storage `[195072]`、权重 `[1536,128]`、输出 `[32,1536]`。195,072 与 packed buffer 的偏移跨度一致，但单靠这个数字不能伪造逻辑 stride/shape，当前保持无张量契约，等待显式源码视图声明。
- **MLA 实际有效头数与旧声明不同**：c32/p4k 首个 MLA 层先由 MlaPrologV3 产生 16 个 head slot，原始 Slice 明确截为 12，再 Pad 回 16 后进入 FIA；V 展开使用 `[12,32,512]×[12,512,128]`，输出投影 K=1,536。旧 case 的通用 MLA 输出宽度是 16×128=2,048。不能把 FIA 的 16 个 padded slot 当作 16 个有效 head。
- **同形矩阵的角色仍需源码边界**：该 MLA 层独立 `[32,7168]→[32,1536]` 的矩阵被旧张量候选列为 q_a，但 MlaPrologV3 已包含 q_a 的权重。其后 Sigmoid/Mul 指向输出 gate 用途，需要源码对应确认，不能将同形候选升级成确定角色。
- **router 输出精度**：原始 BF16×BF16 的 router 输出为 FLOAT，旧声明输出 BF16。应修输出契约，不应把 compute 格式直接改成 FP32 来套用 router 小 tile。

上述 c32/p4k 的逐行 ABI 与源码身份见 [bounded evidence](kimi-c32-projection-bounded-evidence.json)；其中单层 MLA 的详细前缀只是一个明确标注的真实样本，其他 12 源的 MatMul 全分区则具有完整人口。

## 旧 DP4 p32k 不混入这 12 份

旧 canonical 算子报告的声明 context 是 **8**，对应的最新 Body 输入是 **32,768**。本轮显式换到 32,768 并重新检查全部候选后，五个旧矩阵组均因契约或候选集合变化被拒绝，另外七个非矩阵组主动排除。没有任何合格新成本 worker，因此不会将旧 context=8 的成本标作新 p32k 成本。独立审核 432 项通过，原 63 个 Body 保留为实测证据；[新排除账本](../acceptance-20261030-kimi-p32k-operators-86c1ee8f/body-operator-family-scoreboard.json) 明确记录这一覆盖缺口。
