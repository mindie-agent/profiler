# GLM：完整 native ABI 分组的资源参考对账

9 个既有 A5 GLM 源、318 次完整 Forward、27,666 个事件，现在全部进入同人口的条件资源参考：36 个 ABI/结构区域组，逐组核对所有对应层的新声明物理工作量，再执行 27 个不同程序集合。Runtime 固定为 `c2261d63fecb01f766207b354244ac995712d100`；本轮新成本执行 7.456 秒，峰值 177.41 MiB。旧 14 源 strict 预测没有重算。

原生描述和完整整数时长直方图来自 [P1 定向分组](../acceptance-20261030-glm-native-partitions/)，此成本阶段没有读原始 CSV。先做 c64 pilot（3 个程序集合、1.101 秒）验证接口，再统一运行九源；以下正式账单只使用九源统一结果，不重复计入 pilot 人口。

| Case | Native | 次/F | 实测 Mean / P50 us | Sim 条件参考 us | 参考−实测活动 ms/F |
| --- | --- | ---: | ---: | ---: | ---: |
| c1 / B1 q4 | GroupedMatmulSwigluQuantV2 | 42 | 33.520 / 33.429 | 20.049 | -0.566 |
| c1 / B1 q4 | SparseFlashMla | 11 | 51.517 / 51.481 | 2.122 | -0.543 |
| c1 / B1 q4 | RecurrentKda | 34 | 13.004 / 12.695 | 4.202 | -0.299 |
| c32 / B32 q4 | GroupedMatmulSwigluQuantV2 | 42 | 207.865 / 207.616 | 159.681 | -2.024 |
| c32 / B32 q4 | SparseFlashMla | 11 | 153.517 / 153.209 | 67.895 | -0.942 |
| c32 / B32 q4 | RecurrentKda | 34 | 43.987 / 44.073 | 53.120 | +0.311 |
| c64 / B64 q4 | GroupedMatmulSwigluQuantV2 | 42 | 211.089 / 210.723 | 161.025 | -2.103 |
| c64 / B64 q4 | SparseFlashMla | 11 | 288.254 / 285.492 | 135.791 | -1.677 |
| c64 / B64 q4 | RecurrentKda | 34 | 78.338 / 78.285 | 103.616 | +0.859 |

GMM 的 Mean/P50 是 KDA/MLA 两个完整 FFN 区域直方图的精确合并；单次预测来自相同物理程序集合，不把某一区域样例外推整族。全部逐组结果与源/声明/运行时身份见 [JSON](glm-native-reference-scoreboard.json) 和 [完整表](glm-native-reference-scoreboard.md)。这九源包含 c1/c3 两份旧采集及七份 ws9 采集；客户端 c3 仍明确是实际 B4，不与另一个 c4 场景合并。

三类条件边界分别为：

- **GMMswiglu V2 FP8 MX**：真实 ABI 是 FP8 输入/权重与 E8M0 分组尺度，完整验证 packed NZ 权重和输入/输出尺度后，对应现有 `expert_up → expert_act → expert_down.quantize` 语义子图。路由 group-list 的值没有保留，缓冲区行数不证明有效 routed rows。当前 Sim 原生融合流量配方只覆盖 INT8/INT4；因此这里执行现有未融合资源参考，不冒充原生 FP8 融合调度与中间 HBM 消除已经建模。
- **SparseFlashMla**：验证 Query/Output、共享 BF16 paged KV、block table、prefix、长度描述、sink 和 metadata 的全部 18 输入/2 输出。c64 一次原生调用对应全部 64 个已声明 sequence attention 程序，采用共同资源下的 graph cost；不是只取一条 sequence，也不是单次结果乘 B。索引容量 2051 与声明 top-k 2048 并列保留，实际有效长度/metadata 数值和 mask/window 标量未知。
- **RecurrentKda**：验证 gate/beta、A_log/dt_bias、QKV/state backing、sequence prefix、state slots 和非空 accepted-token 描述。对应已有整体 gating/normalization 与所有 sequence scans。原生存在 accepted-token 输入，而现有 arch35 source adapter 明确不支持该 state-slot 分支；因此没有绕过其约束或把输入设空，也没有将 flat backing extent 解释为完整 active stride。

所有新行都标记 `reference_only`，不增加 strict 通过数。活动差额有并行重叠，不能相加解释 Body wall span，也不能以此反推通信带宽或固定等待。

三个真实数据回归覆盖：2,697 个 c64 事件直方图与全 batch 范围完整保留；任一层新物理工作量不同则拒绝把原全组直方图切给它；FP8 weight-scale 布局改变不会被误解释成 W4A8。加上既有 GLM 诊断测试，6 项通过。

独立审核通过 31,047 项检查、0 失败，含 30,171 项 fresh 逐层资源一致性检查；审核不重读原始采集、不重跑成本，峰值 87.77 MiB，详见 [审核回执](glm-native-reference-independent-review.json)。

统一主表通过 `references` 输入导入这 36 组，保持独立的运行时与条件边界。外部参考按实测源/几何、原生算子、角色、层集合以及完整观测 ABI 的哈希选择最新输入，不受普通 operator receipt 的选择结果过滤；观测 ABI 不含预测物理工作量。各组 Mean/P50 和调用数原样保留，既有 strict 评分分母不变。

运行入口为 `compare_glm_native_partitions.py --partition ... --output-dir ... --runtime-source-commit ...`。每个源在独立子进程执行，默认预算 180 秒、512 MiB；失败会显式保留且 CLI 非零退出。原先 strict 表和原观测制品不受影响。
