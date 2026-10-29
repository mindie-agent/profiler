# GLM：matrix-mapping 修正后的算子账单

本臂固定 Sim `86c1ee8f18b9b997eacb315476e2461b99b59fb1`，复用原始实测直方图，重新导出声明和物理工作量并执行成本程序。没有重扫 CSV，也没有复用旧预测。下列 `ms/F` 是算子活动量差，不能相加解释 Body wall span；通信中的对端等待和并发覆盖也不能据此消除。

| 独立采集组 | 选中 / 全部 Forward | Strict 通过 / 对比 | ≤50 us 档 | >50 us 档 | 峰值 MiB | 独立检查 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [原 GLM 11 源](glm-operators-86c1ee8f/body-operator-family-scoreboard.md) | 393 / 511 | 193 / 217 | 193 / 206 | 0 / 11 | 198.16 | 10,163 / 0 fail |
| [A5 c1、c3](glm-low-concurrency-86c1ee8f/body-operator-family-scoreboard.md) | 118 / 118 | 37 / 38 | 37 / 37 | 0 / 1 | 119.72 | 1,814 / 0 fail |
| [A3 c16 livepre](glm-a3-livepre-86c1ee8f/body-operator-family-scoreboard.md) | 37 / 108 | 20 / 21 | 20 / 21 | 0 / 0 | 112.45 | 869 / 0 fail |

微算子采用单次绝对误差 ≤15 us；较大算子采用相对误差 ≤15%。客户端 c3 的实际执行是 B4、q4；A3 livepre 是 B16、q6。后者原 operator 声明的 context 为 4096，A5 c1/c3 为 4104；保持原条件，不能冒充 A3 Body 的 4104 同几何对账。观测没有给出精确 active KV 长度。

## 已严格比较的主要差额

表中 Mean/P50、调用数和预测覆盖同一实测子集。误差是 `预测 service − 实测 activity`。

| Case | Native / 声明 role | Mean / P50 us | 次/F | Sim us | 差 ms/F |
| --- | --- | ---: | ---: | ---: | ---: |
| A5 c64 | GroupedMatmul / expert_down | 115.777 / 117.337 | 42 | 90.476 | -1.063 |
| A5 c64 | HcPost / attention.hc_post_group | 11.932 / 12.155 | 45 | 5.585 | -0.286 |
| A5 c64 | RmsNorm / norm2 | 6.345 / 6.415 | 45 | 1.312 | -0.226 |
| A5 c32 | GroupedMatmul / expert_down | 109.824 / 110.413 | 42 | 87.876 | -0.922 |
| A5 c32 | MatMulV3 / linear_qkvbfg_a | 26.517 / 26.599 | 34 | 16.566 | -0.338 |
| A5 c32 | HcPost / attention.hc_post_group | 8.079 / 8.107 | 45 | 2.793 | -0.238 |
| A5 c1 | GroupedMatmul / expert_down | 22.482 / 22.473 | 42 | 8.800 | -0.575 |
| A5 c1 | MatMulV3 / router | 8.756 / 8.743 | 42 | 16.544 | +0.327 |
| A5 c1 | MatMulV3 / linear_qkvbfg_a | 16.983 / 16.915 | 34 | 8.208 | -0.298 |
| A5 c3 / B4 | GroupedMatmul / expert_down | 51.524 / 51.382 | 42 | 34.955 | -0.696 |
| A5 c3 / B4 | MatMulV3 / router | 9.420 / 9.392 | 42 | 20.437 | +0.463 |
| A5 c3 / B4 | MatMulV3 / linear_qkvbfg_a | 17.826 / 17.762 | 34 | 9.002 | -0.300 |
| A3 c16 livepre | HcPost / attention.hc_post_group | 20.206 / 19.701 | 45 | 6.703 | -0.608 |
| A3 c16 livepre | MatMulV2 / index_k | 7.501 / 8.160 | 22 | 35.103 | +0.607 |
| A3 c16 livepre | HcPost / ffn.hc_post_group | 20.082 / 19.840 | 45 | 6.703 | -0.602 |

完整逐源 Top 3、原始精确值、P50 population、语义区域和原成本分区一致性见 [11 源诊断](glm-gap-86c1ee8f.md)、[低并发诊断](glm-low-concurrency-gap-86c1ee8f.md)、[A3 livepre 诊断](glm-a3-livepre-gap-86c1ee8f.md)。

## 未严格评分的最大活动量

下表不是预测误差。角色和区域来自已保存的整体结构拆解，不能由 kernel 名字倒推层号。

| A5 c64 native family | Mean / P50 us | 次/F | 实测活动 ms/F | 当前证据与下一步 |
| --- | ---: | ---: | ---: | --- |
| GroupedMatmulSwigluQuantV2 | 211.089 / 210.723 | 42 | 8.866 | 既有归档 contract 未解析、无全量 ABI 分桶；先定向补保存 native ABI 与路由有效行，复用 Sim 融合配方再绑定。不能把缓冲容量当有效 token 数。 |
| SparseFlashMla | 288.254 / 285.492 | 11 | 3.171 | 已有样例完整 native ABI，但无同 ABI 的全量直方图分区；先定向补档，再验证当前声明适配域。不能用一个样例扩展整族。 |
| RecurrentKda | 78.338 / 78.285 | 34 | 2.664 | 保留的合同未解析；先核 source ABI、状态布局和 q/B，再显式选择已有 KDA source 程序。当前没有可声称严格误差的预测。 |

A3 livepre 的 `GroupedMatmulSwigluQuant` 有完整参数级 cohort，但原生融合与声明未融合子图边界不同：142.415 us Mean、142.163 us P50、42 次/F；声明参考 285.783 us，参考活动差 +6.021 ms/F。该值保留为 `reference_only`，用于定位融合资源配方差异，不进入 strict 达标分母。

A3 `KvQuantSparseFlashAttentionVllm` 的本地私有实现仍未找到。公开近名 arch22 源码要求 672 字节 stride、scale offset 640 与独立 rope 条件；实测 INT8 528 字节行且没有相应 rope 输入。不能把公开近名实现当作这次调用的实现证据。此短查只读现有本地仓库和采集元数据，没有远端或补采。

## matrix-mapping 变化的受控验证

`67 → 86` 包含多项运行时变化，不能全归因于 `83f720ae`。独立执行的 [同运行时、同声明矩阵对照](glm-underfilled-controls-86c1ee8f.md) 只改变 `underfilled_candidates`，保持 dtype、narrow candidates 和其余配方不变，共 321 次成本执行，峰值约 70.6 MiB。

以 A5 c32 为例：FP32 router 默认 19.750 us，关闭 underfilled 后 159.682 us；正确的小 tile 收益保留。BF16 index_k 默认 16.431 us、显式 underfilled 3.026 us；FP8 shared gate_up 默认 8.505 us、显式 underfilled 3.154 us；BF16 KDA 大投影 16.566 us 没有变化。这是声明程序的候选域实验，不是原生 tiling 已被实测证明。

原 11 源 strict 从 67 代的 197/217 变为 193/217，四个新增失败全部是 A3 BF16 index_k；其每次预测分别从 7.525/10.047/15.091/20.174 us 上升到 27.695/35.375/40.495/40.495 us。保留这个真实退化，不为达标恢复超出适用域的候选。A5 FP32 router 改善仍保留，c4–c64 shared gate_up 活动预测增加 0.130–0.225 ms/F，仍通过微算子容差。

复现诊断只读取已保存 JSON；调用 `diagnose_glm_family_gap.py --report ... --baseline-report ... --output ...`。只有显式传 `--matrix-control-case` 才执行新的声明矩阵成本。原观测、原成本与新臂身份独立保存。
