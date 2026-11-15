# 原生算子校准适配器与执行条件边界

`native_observations.py` 是面向离线采集回放的 `observed_native` 输入适配器。它在调用 `body.predict_body` 之前，将采集记录中已声明的物理执行条件绑定到仿真输入副本上，既不修改原始 CSV、观测摘要或 Body 计时边界，也不向常规 `mindie-sim` 预测入口强加额外的实测准入条件。多代际离线回放入口（`wave5_generalization_eval.py` 与 `dsh_generalization_eval.py`）通过该适配器运行新预测；仅做历史报告汇总时不会事后补写新的校准身份。

每次回放均分别记录 `mindie-sim` 包内容哈希与 `native_observation` 校准身份哈希（覆盖适配器源码、各芯片导入器及 Profile JSON）；一旦校准代码或参数发生变更，旧预测缓存自动失效。每份 Profile 均完整记录训练源与验证源路径、原生 CSV 行号、SHA256、输入张量 ABI 及尚未确认的外部条件；未知的算子编译二进制身份一律作为显式限制保留，绝不冒充已获实测证明的源码等价关系。

## 已落地的物理边界修正

- **A2 `LightningIndexer` 与 `SparseFlashAttention` 分离校准**：A2 `LightningIndexer` 采用完整 LI 子图边界，`SparseFlashAttention` 独立建模校准。匹配键包含有序的 Query/Context 分区与压缩比，防止将总配对数相同但批次结构不同的负载混用。量化输入按算子实际角色严格区分 BF16 Indexer、BF16 MLA Absorb 与仅带 Scale 的 INT8 权重列；默认 INT8 `scale+offset` 契约保持不变，遇到显式声明冲突时保留调用方原始声明而不强行覆盖。
- **A2 Prefill 与 `q=1` Decode 独立建模**：A2 Prefill 与 `q=1` Decode 使用各自独立的校准 Profile；Decode 阶段的融合 `MlaPreprocess` 不拆解为 Prefill 阶段的独立矩阵乘法调用。集合通信响应显式保留通信量（Payload）、并行组规模与传输链路条件，绝不把整网 Body 未解释残差摊入每层 `AllReduce`。
- **A5 `q=1` GDN 五边界联合准入**：A5 `q=1` GDN 校准仅在五个完整原生算子边界同时匹配时才替换默认解析规则，由有效序列数、物理张量形状、算子调用实现与硬件服务条件共同锁定适用域；未命中时完整保留调用方原始输入与默认预测路径，不删改真实的 `route_normalize` 节点。
- **A5 `q=4` 有效行与图捕获填充槽位分离**：A5 `q=4` 采用独立的 FlashAttention / 递归状态响应，显式区分有效 Query 行、图捕获物理槽位与零长度填充序列。Qwen3.6 完整 `64K` 采集组与 Qwen3.5 完整 `192K` 采集组严格留作验证集，其原生实测耗时不参与训练曲线拟合。
- **Qwen3.5 非融合 MC2 有效路由行与分配容量分离**：显式区分有效 `group-list` 行数与预分配接收容量。例如 `q=28 / physical=32` 场景保留 `56` 行有效专家计算与 `256` 行接收缓冲区容量：分组矩阵乘（GEMM）按有效行执行，`SwiGlu` 与动态量化按完整缓冲容量扫描，同时保留 FP32 Router 与 `FP32 -> BF16` 权重 Scale 类型转换。该规则要求启动命令显式声明开启 `force-EPLB` 且关闭 `GMMSwiGLUQuant` 融合；若存在显式配置冲突则保留原输入。`q=1` 下的六个 `L=8` 物理域（`E32/K2/B4`、`E32/K4/B1`、`E64/K4/B4` 以及 `B16` 下的 `E32/K2`、`E48/K2`、`E48/K4`）使用独立于 `q=4 / E256` 的专属 Profile：全部 `34` 个参数仅由六份 `4K` 采集中的 `66,176` 次完整原生调用按 `count/sum` 池化标定，六份 `64K` 采集中的 `60,096` 次调用仅用于留出验证（验证集中命中的 `48` 个原生边界均值误差以及 `12` 份训练/验证采集的 `15` 个样本桶与加权均值误差均在 `10%` 以内）。对于 `E48/K2/B16` 的 `64K` 采集，其中共现的 `B13/B15/B12` 样本桶不在该套 Profile 适用域内，即使 `B15` 局部 GMM 形状与 `B16` 兼容也不外推扩域，原输入与预测路径保持不变。注意：此处 `64K` 仅针对本次八条原生响应做局部留出，底层基准模型仍含样本内校准成分，不能据此宣称整网零样本独立泛化。
- **图捕获物理缓冲区与零长度尾槽位**：图捕获描述符严格区分有效 Query 行与捕获的物理缓冲行数。完整图内的 GDN 拷贝、门控（Gating）与 Q/K 归一化按物理缓冲区尺寸计费；末尾重复的序列偏移代表零长度填充槽位，不产生额外的因果卷积或递归状态更新工作量。
- **从 `cmd.sh` 字面量导入编译与分桶配置**：A2/A3/A5 回放直接解析目标采集目录下的 `cmd.sh` 获取字面量图编译槽位，绝不凭模型名称或实测耗时反推捕获桶大小，未声明字段统一标记为 `not_provided`（修复了早期 A3 中 `188` 份采集沿用其他部署模板将单行 `q=1` 误设为 `4/8` 行最小捕获桶的问题）。对于已选用 `vllm_ascend_mc2_tp_slice` 但未显式声明填充策略的调用方，按固定框架源码版本补齐 `right_to_tp` 并单独记为源码条件（该对齐仅作用于 Router 之后的 MoE 局部切片：A3 `q=1/4` 下 Router 与共享专家仍保持 `1/4` 行，`prepare` 向上对齐至 `8` 行后按 `TP8` 切分为每卡 `1` 行，`finalize` 再裁回原始行数）。原始 `PadV3` 与源码物化算子仅核对输入/输出行边界，不声称编译二进制完全等同。

## 为何整网均值达标不能替代逐样本群与逐分块验收

1. **禁止将首层初始化空泡均摊进稳态算子**：早期部分历史报表中曾将首次执行等待均摊进常规通信算子。例如 A3 `synth_qwen35_L8_E16_K2_tp8ep8_prefill_4k_c1` 中，旧版 `AllReduce` 响应每次计入 `92 ms`，而真实采集中的两段主要空窗实际发生在首层状态 Gather/Scatter 访问之前——虽然整步总耗时看似接近，但前后两个 Chunk 的预测误差方向完全相反。当前原生校准仅提取完整 Kernel 净观测耗时，绝不吸收此类空窗。
2. **相同静态输入下的运行时状态分叉**：存量采集中存在静态预测输入完全一致、但设备运行状态截然不同的真实案例。例如 A3 `qwen38_tp8_mtp3_prefill_192k_c1` 与 `qwen38_tp8_mtp3_prefill_256k_c1` 的首个 Prefill 分块均为 `q=8192, context=0`，且启动命令声明了相同的 Decode 图捕获槽位 `[1,2,4,8,12,16,24,32]`（静态模板与预测几何 SHA256 均为 `11c9b780614a562a0a761978b11f0f60a419365fe366a7fd8e784be76a41b15b`），但纳秒区间并集实测结果如下：

| 保留实测窗口 | Body 墙钟跨度 (ms) | 设备活动并集 (ms) | 内部未覆盖空窗 (ms) |
| --- | ---: | ---: | ---: |
| `192K` 采集首块 (`q=8192, ctx=0`) | 3221.954126 | 425.961623 | 2795.992503 |
| `256K` 采集首块 (`q=8192, ctx=0`) | 426.426140 | 425.334521 | 1.091619 |

上述数值直接来自原始采集的纳秒区间并集：既不能人为抹除 `2795.99 ms` 空窗后声称原始 Body 达标，也不可能用同一个单值确定性预测同时落在两份实测的 `±10%` 区间内。唯有显式引入首次编译缓存、图捕获初始化或外部等待归属状态，才能解释此类差异；仅凭汇总 API 耗时表或客户端 SSE 到达时间戳无法还原逐次调用与逐卡等待状态。因此，验收报表必须同时保留采集加权误差、主样本群误差及逐个样本桶/分块明细。

## A3 部署输入修正与尚未覆盖的服务边界

- **`EP=TP` 并行拓扑还原（`capture_policy.py`）**：A3 `synth_qwen35_L8_E32_K2_tp8ep8_decode_256k_c1` 的旧模板曾误用 `EP=1`（32 个本地专家、64 维分片中间层），而真实启动命令与 CSV 实为 `EP=8`（4 个本地专家、完整 512 维中间层，含 MC2 `Dispatch/Combine/AllGather`）。`capture_policy.py` 现直接解析命令中显式声明的 `TP`、`DP` 与 `EP` 开关，仅在 `DP=1, TP>1`、显式启用 EP 且 MoE 拓扑受支持时推导 `EP=TP` 并替换继承的 `tp_join_reduce`；声明值、推导值、缺失项与修改前后快照均独立记录，遇到重复或动态参数立即报错。
- **CSV 算子描述符流式核验（`capture_structure.py` & `capture_ffn_guard.py`）**：针对上述拓扑修正，`capture_structure.py` 流式核对目标 CSV 中的 `Dispatch/Combine`、分组矩阵乘与 `prepare` 边界，仅在描述符受支持且前后一致时绑定 `MC2 TP slice` 调用方；若窗口内混入其他版本的 Routing/Finalize 或 Token Permutation 路径则拒绝绑定，绝不将混合或未覆盖 ABI 伪装为匹配成功。原生 GMM 的 `16` 行仅代表预分配容量而非真实激活 Token 数；整份 `E32` CSV 中的 `2,124` 次 `AllGather` 亦不盲目全数归入 MoE。`capture_ffn_guard.py` 进一步比对修正前后的专家矩阵静态维度，仅停用维度已失效且缺少对应维度守卫的旧版路由 FFN 规则，不引入任何耗时凑数或 Body 残差补偿。
- **保留在完整分母中的已知未达标项**：现有 `arch22_v2_caller` 虽能表达源拓扑的逻辑工作量下界，但需要独立声明 `peer window`（本适配器不代填默认值；此前四个未校准源拓扑反事实推演值为 `2.6015–2.9036 ms`，低于实测 `3.5675 ms`）。此外，该采集首次 `AllReduce` 均值高达 `520.378 µs`（其余调用均值 `9.196 µs`），等待根因尚未确认，严禁硬编码首层固定补偿；DeepSeek-V4.1 的真实 `graph1` 与 MC2 局部 `pad8` 同样暴露了原生输出投影、SFA 与 MC2 局部欠算问题。上述未达标项均如实保留在完整验收分母中。

## 尚未覆盖的 Eager 路径与等待状态漂移

Qwen3.5 `q=64` 的三份 Eager 模式采集实际走 `ALLGATHER` 路由路径（`DP=1`、非序列并行下保留完整 `64` 行，按 EP 本地专家筛选并在共享/路由专家汇合后执行 TP `AllReduce`；CSV 中为 `MoeInitRoutingV3` / `MoeFinalizeRoutingV2`，不含 MC2 `Dispatch/Combine`）。因此这三份采集不套用 MC2 Profile，并原样保留在全量验收分母内。其 `39` 个完整 Forward 呈现出“前期 `AllReduce` 短而层内空窗长、后期 `AllReduce` 长而层内空窗短”的交替漂移，且保留的 Host API 汇总表仅有累计耗时与总调用次数（每步 Host `AllReduce` 记为 `90` 次，而目标 Body 内原生调用为 `80` 次），故不能将 API 汇总耗时直接摊入目标 Body。

## 捕获级作用域（Per-Capture Scope）与两阶段原生适配集成

`scoped_native_replay.py` 为单份采集构建一次性的预处理作用域（Prepared Scope），并针对每个实际几何窗口依次执行两阶段适配：

1. **阶段一（结构调用方声明，`capture_scoped_structure`）**：按当前窗口的实际几何绑定对应的图结构与通信物化方式；
2. **阶段二（原生算子响应绑定，`prefill_native_observations`）**：在不改写实测值、Forward 计数、上下文长度与计时边界的前提下绑定匹配的 FlashAttention / `AllReduce` 物理响应。

由此，同一份超长上下文采集中首块 `q=8064, context=0` 与尾块 `q=256, context=399744` 可各自保留独立的 `gather_output_materialization`（分别为 `per_rank_copy` 与 `view`），避免将单一窗口的局部声明错误提升至整份采集。预处理作用域在单份采集内仅构建一次，并在仿真作业实例化完成后立即释放内存。

- **截断 Prefill 上下文校验与有界读取**：A5 截断 Prefill 的 `context_offset` 仅在 Forward 缺少显式上下文记录时按 `requested_context - sum(query_rows)` 推导，显式观测到的上下文绝不平移；若精简证据中显式记录的 `context_tokens`、`phase` 或并发序列数与预处理几何不一致，在进入定价前即报错拦截。缺失采集或陈旧解析器缓存分别如实标记为 `not_provided`、`unbound` 或 `stale`；完整提取文件读取上限为 `16 MiB`，先执行流式字段投影再解析 JSON。
- **缓存身份失效联动与适用限制**：`native_observations.PROFILE_FILES` 同时纳入捕获级结构声明模块（含 `capture_scoped_geometry.py`）、原生算子响应构建器、共享回放辅助模块及驱动脚本，任何一处代码或 Profile JSON 变动都会自动更新缓存身份哈希（当前 `pyproject.toml` 将 `mindie-sim` 锁定至提交 `dccea42b086fa5abd315c44dded188ed1e0347f8`）。生成图校验仅将 `mindie-sim` 实际产出的 `balanced_grouped_gate_up` 与 `balanced_grouped_down` 映射为同一分组矩阵乘语义角色，其余 Recipe 名称不做模糊前缀匹配，且逐层严格核对专家数与隐藏层维度。A3 混合 Fixture 的完整分块现可同时应用上述两阶段适配；A5 归档模板中继承的 `alltoall` 仅在显式声明 `archive_template=True` 时替换为 `local_expert_reduce`（四个历史 `E48` 采集的模板继承关系完整记入溯源字段，不冒充原生开启 `force-EPLB`）。当前限制依然明确：A2 暂不在捕获级结构调用方适用域内，算子编译二进制等价性、真实 `group-list` 分布、逐次 Forward 误差与盲测独立泛化均未宣称已获证明。
