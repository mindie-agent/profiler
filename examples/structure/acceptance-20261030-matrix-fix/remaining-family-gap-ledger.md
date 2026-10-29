# 修正后剩余算子账单

仅消费已冻结的 Kimi12 与 GLM9 证据：Kimi 618 次、GLM 318 次完整 Body。没有新增 raw 扫描或成本执行。Body 对照固定 67 与 corrected86；GLM 新原生参考成本为 c226，身份分别保留。logical96 新结构将另立新臂，本表保留 corrected86 参考。

下列正差为 **实测算子活动 − 声明 service**，单位 ms/F；不能相加解释 Body wall span，也不能把整个 67→86 变化归因于83。排序包含严格 tensor cohort 与明确标出的条件参考，不是达标失败榜；微算子单次误差仍按15us容差。

| 模型 / 采集人口 | Top 1 ms/F | Top 2 ms/F | Top 3 ms/F |
| --- | --- | --- | --- |
| Kimi K3 A5 BF16 / 12 源、618 F | GroupedMatmul / expert_up (条件) **1.217306** | MatMulV3 / latent_down (严格) **0.968498** | MatMulV3 / latent_up (严格) **0.651216** |
| GLM Flash A5 45 layers / 9 源、318 F | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) **1.522938** | GroupedMatmul / expert_down (严格) **0.739843** | SparseFlashMla / indexed_attention_batch (条件) **0.717829** |

## 逐源 Body 与同方向 Top3

每源 Body 观测、q/B、case 字节及 Forward 分母在两代完全一致。Δ 是 corrected86 预测减去67预测；operator Top3 仅覆盖有合法成本的原生事件分区。

| Case | F | B / q | Real Body ms | Sim67 → Sim86 ms | Δ ms | Top 1 ms/F | Top 2 ms/F | Top 3 ms/F |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Kimi c16_p16k | 47 | 16 / 1 | 39.247 | 23.145 → 27.200 | +4.056 | GroupedMatmul / expert_up (条件) 1.982689 | MatMulV3 / latent_down (严格) 1.025320 | GroupedMatmul / expert_down (条件) 0.809945 |
| Kimi c16_p4k | 49 | 16 / 1 | 36.985 | 21.934 → 25.990 | +4.056 | GroupedMatmul / expert_up (条件) 1.976109 | MatMulV3 / latent_down (严格) 1.022362 | GroupedMatmul / expert_down (条件) 0.811831 |
| Kimi c1_p16k | 59 | 1 / 1 | 30.823 | 18.977 → 23.096 | +4.119 | MatMulV3 / latent_down (严格) 0.898347 | MatMulV3 / latent_up (严格) 0.595751 | GroupedMatmul / expert_down (条件) 0.346452 |
| Kimi c1_p4k | 59 | 1 / 1 | 30.637 | 18.901 → 23.021 | +4.119 | MatMulV3 / latent_down (严格) 0.898407 | MatMulV3 / latent_up (严格) 0.593621 | GroupedMatmul / expert_down (条件) 0.345883 |
| Kimi c2_p16k | 54 | 2 / 1 | 33.876 | 19.199 → 23.319 | +4.119 | MatMulV3 / latent_down (严格) 0.901633 | MatMulV3 / latent_up (严格) 0.611653 | GroupedMatmul / expert_down (条件) 0.362098 |
| Kimi c2_p4k | 55 | 2 / 1 | 33.548 | 19.048 → 23.167 | +4.119 | MatMulV3 / latent_down (严格) 0.903227 | MatMulV3 / latent_up (严格) 0.610803 | GroupedMatmul / expert_down (条件) 0.362093 |
| Kimi c32_p16k | 41 | 32 / 1 | 44.666 | 28.078 → 32.347 | +4.269 | GroupedMatmul / expert_up (条件) 2.054393 | MatMulV3 / latent_down (严格) 1.144731 | GroupedMatmul / expert_down (条件) 0.834905 |
| Kimi c32_p4k | 46 | 32 / 1 | 40.019 | 25.658 → 29.926 | +4.269 | GroupedMatmul / expert_up (条件) 2.056025 | MatMulV3 / latent_down (严格) 1.144706 | GroupedMatmul / expert_down (条件) 0.835818 |
| Kimi c4_p16k | 52 | 4 / 1 | 34.816 | 19.644 → 23.763 | +4.119 | GroupedMatmul / expert_up (条件) 1.785944 | MatMulV3 / latent_down (严格) 0.933667 | GroupedMatmul / expert_down (条件) 0.718670 |
| Kimi c4_p4k | 53 | 4 / 1 | 34.194 | 19.342 → 23.461 | +4.119 | GroupedMatmul / expert_up (条件) 1.764571 | MatMulV3 / latent_down (严格) 0.938239 | GroupedMatmul / expert_down (条件) 0.715755 |
| Kimi c8_p16k | 51 | 8 / 1 | 35.964 | 20.533 → 24.652 | +4.119 | GroupedMatmul / expert_up (条件) 1.897319 | MatMulV3 / latent_down (严格) 0.951135 | GroupedMatmul / expert_down (条件) 0.762119 |
| Kimi c8_p4k | 52 | 8 / 1 | 34.819 | 19.927 → 24.047 | +4.119 | GroupedMatmul / expert_up (条件) 1.892549 | MatMulV3 / latent_down (严格) 0.951852 | GroupedMatmul / expert_down (条件) 0.764368 |
| GLM c16_p4k | 30 | 16 / 4 | 33.031 | 20.914 → 21.314 | +0.400 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 1.983157 | GroupedMatmul / expert_down (严格) 0.694197 | SparseFlashMla / indexed_attention_batch (条件) 0.579026 |
| GLM c16_p8k | 32 | 16 / 4 | 33.616 | 21.102 → 21.502 | +0.400 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 1.978018 | GroupedMatmul / expert_down (严格) 0.678240 | SparseFlashMla / indexed_attention_batch (条件) 0.582012 |
| GLM c32_p4k | 31 | 32 / 4 | 37.669 | 24.737 → 25.198 | +0.461 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 2.023744 | SparseFlashMla / indexed_attention_batch (条件) 0.941841 | GroupedMatmul / expert_down (严格) 0.921823 |
| GLM c32_p8k | 35 | 32 / 4 | 38.713 | 25.116 → 25.578 | +0.461 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 2.023039 | SparseFlashMla / indexed_attention_batch (条件) 0.939771 | GroupedMatmul / expert_down (严格) 0.923038 |
| GLM c4_p8k | 11 | 4 / 4 | 21.418 | 12.898 → 13.178 | +0.280 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 1.111313 | GroupedMatmul / expert_down (严格) 0.554725 | SparseFlashMla / indexed_attention_batch (条件) 0.487471 |
| GLM c64_p4k | 31 | 64 / 4 | 46.528 | 32.002 → 32.407 | +0.405 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 2.102698 | SparseFlashMla / indexed_attention_batch (条件) 1.677098 | GroupedMatmul / expert_down (严格) 1.062621 |
| GLM c8_p4k | 30 | 8 / 4 | 28.833 | 18.156 → 18.482 | +0.327 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 1.815249 | GroupedMatmul / expert_down (严格) 0.619399 | SparseFlashMla / indexed_attention_batch (条件) 0.402889 |
| GLM c1 | 65 | 1 / 4 | 15.683 | 9.501 → 9.501 | +0.000 | GroupedMatmul / expert_down (严格) 0.574620 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 0.565784 | SparseFlashMla / indexed_attention_batch (条件) 0.543351 |
| GLM c3 | 53 | 4 / 4 | 21.068 | 14.028 → 14.028 | +0.000 | GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant (条件) 1.119230 | GroupedMatmul / expert_down (严格) 0.695888 | SparseFlashMla / indexed_attention_batch (条件) 0.479785 |

## 方向相反的差值与待补机制

GLM c64/p4k 的条件 GMM gate-up/SwiGLU/量化差为 **2.102698 ms/F**，SparseFlashMla 为 **1.677098 ms/F**，严格 expert_down 为 **1.062621 ms/F**。RecurrentKda 是预测高于实测 **0.859443 ms/F**，方向相反，未计入低估 Top3。

- Kimi expert_up 的条件差依赖声明的均衡有效行数；完整 buffer ABI 不等于实测路由分布。检查 BF16 grouped 的 owner/tile 和有效工作量。
- Kimi latent_down/up 已有严格 tensor cohort；验证实际矩阵 tiling、launch 与融合边界，不能把其活动差直接加回 Body。新 logical96/物理16头 padding 需重新导出匹配，不能沿用旧 MLA 绑定。
- GLM MXFP8 融合 gate-up/SwiGLU/quant 当前仍采用未融合程序集参考，内部 HBM 与 launch 尚未消除；需要对应 FP8 原生融合配方。
- GLM SparseFlashMla 的2051是索引容量，不能当实际稀疏长度；完整 ABI 允许条件 full-batch 对照，native gather/split/metadata 仍需源码对应。
- GLM KDA 的 accepted-token/state-slot 分支尚缺源码适配，值与布局不全时保留条件参考，不强行严格评分。

精确每次 Mean、调用数、正负差、source/case/runtime/hash 与可实施 Sim 文件入口见 [JSON](remaining-family-gap-ledger.json)。完整独审：[Kimi4969项](kimi-family-gap-independent-review.json)、[GLM31047项](../acceptance-20261030-glm-native-references-c2261d63/glm-native-reference-independent-review.json)。
