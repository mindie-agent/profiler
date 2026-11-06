# 原生算子校准与执行条件

`native_observations.py` 是离线 capture 回放的 `observed_native` 输入适配器。
它在现有 `body.predict_body` 之前绑定已声明的物理条件，不修改原始 CSV、
观察摘要或 Body 计时边界，也不向普通 Sim 预测加入测量准入要求。
Wave5 重跑入口和 DSH 新预测使用这个适配器；聚合已有报告不会补写新校准身份。

每次运行分别记录 Sim 内容身份和 native observation 身份。后者覆盖适配器代码、
各硬件导入器和 profile JSON；校准变更不能复用旧预测缓存。profile 内保留训练与
验证来源、原生行号、SHA256、输入 ABI 和尚未确认的条件。未知编译二进制身份
作为限制保留，不冒充已经实测证明的源码等价关系。

## 已实现的边界修正

- A2 LightningIndexer 使用完整 LI 边界；SparseFlashAttention 单独校准。
  匹配包含有序的 query/context 分区和压缩比例，避免相同 pair 数的不同批次混用。
  量化输入按实际角色区分 BF16 indexer、BF16 MLA absorb 和只含 scale 的 INT8 权重列。
  默认 INT8 scale+offset 合同保留，显式声明冲突不会被校准覆盖。
- A2 Prefill 与 q=1 Decode 使用不同 profile。Decode 的 MlaPreprocess 不拆成
  Prefill 的独立矩阵调用。通信响应保留 payload、并行组和 transport 条件，
  不把完整 Body 残差填进每层 AllReduce。
- A5 q=1 GDN profile 只有在五个完整原生边界均匹配时才替换旧规则。
  有效序列、物理形状、调用实现和硬件服务条件共同限定适用域。
  未命中时保留调用者的原始输入与预测路径，不删除真实的 route_normalize。
- A5 q=4 使用独立的 FlashAttention/递归响应，显式区分有效 query 行、
  捕获槽位与零长度填充序列。Qwen3.6 的完整 64K capture 组与 Qwen3.5 的
  完整 192K 组留作验证，其原生耗时不进入训练曲线。
- Qwen3.5 非融合 MC2 调用显式区分有效 group-list 行与分配容量。
  q=28/physical=32 的源 mask 保留 56 行有效专家计算和 256 行接收容量；
  GEMM 按有效行执行，SwiGlu/量化扫描完整容量，并保留 FP32 router 及
  FP32→BF16 权重 scale Cast。导入要求实际命令声明 force-EPLB 开启、
  GMMSwiGLUQuant 融合关闭，显式冲突保留原输入。
  q=1 的六个 L8 物理域使用独立 profile，与 q=4 的 E256 数据分开：
  E32/K2/B4、E32/K4/B1、E64/K4/B4，以及 E32/K2、E48/K2、E48/K4
  的 B16。34 个参数只由六个 4K capture 的 66,176 次完整原生调用按
  count/sum 池化赋值；六个 64K capture 的 60,096 次调用仅用于验证。
  这六个验证 capture 中实际应用的 48 个原生边界均值均在 10% 内；
  12 个训练/验证 capture 的 15 个 population 及各 capture 加权均值也
  均在 10% 内。E48/K2/B16 的 64K capture 同时含有效 B13/B15/B12，
  这些 population 不在整套 profile 的适用域，完整输入和预测保留原样。
  B15 的局部 GMM 形状虽与 B16 兼容，也不据此扩大整套适用域。
  同物理 ABI 共用响应，KV context 不选择这些局部 MoE 算子的参数；
  没有按 Body 残差或 capture 名称选择曲线。64K 只对本次八条原生响应
  整体留出，底层历史校准仍属 in-sample，不能据此宣称整模型独立泛化。
- 图捕获描述符区分有效 query 行与捕获的物理行。完整图中的 GDN 拷贝、
  gating 和 Q/K normalization 保留物理缓冲区；重复的末尾序列偏移表示
  零长度槽位，不产生额外卷积或递归状态工作。
- A2/A3/A5 回放从调用者选定 capture 的 `cmd.sh` 导入字面量编译配置。
  不根据模型名或观察耗时猜捕获桶；未声明字段保留为 `not_provided`。
  A3 中已有 188 个 capture 的旧模板桶与真实命令不同，例如实际 q=1
  卷积/递归输入仅一行，旧模板却从另一部署继承了最小 4/8 行捕获桶。
  对已经选择 `vllm_ascend_mc2_tp_slice`、但未声明 padding 的调用者，
  同时按固定源码版本补齐 `right_to_tp`，并单独记为 source condition。
  这是 router 之后的 MoE 局部对齐，不改变字面量图捕获槽位：A3 实际
  q=1/4 的 router 和 shared 均保持 1/4 行，prepare 扩为 8 行后按 TP8
  切成每 rank 1 行，finalize 再裁回原行数。显式 padding 和非 MC2 调用保留。
  原始 PadV3 与所选源码的物化算子只核对输入/输出行边界，未声称二进制相同。

## 为什么整网总误差不能替代逐群验收

旧 Wave5 表中存在把首次等待均摊到普通算子的记录。例如 A3 的
`synth_qwen35_L8_E16_K2_tp8ep8_prefill_4k_c1`，旧 AllReduce 响应为每次 92 ms，
而两个主要空窗实际位于首层 gather/scatter 状态访问之前。总时长可以因此接近，
两个 chunk 的误差却方向相反。新的原生响应只取完整 kernel 观测，不吸收这些空窗。

保留数据还存在相同预测输入、不同运行状态的情况。A3
`qwen38_tp8_mtp3_prefill_192k_c1` 与 `qwen38_tp8_mtp3_prefill_256k_c1`
的第一块均为 q=8192/context=0。两份真实命令均声明完整 Decode 捕获及
`[1,2,4,8,12,16,24,32]` 槽位。在仅导入图字段的历史基线中，完整模板与
预测几何的 SHA256 均为
`11c9b780614a562a0a761978b11f0f60a419365fe366a7fd8e784be76a41b15b`；
后续输入修正以每轮全量回放记录的完整输入身份重新检查。

| 保留观测 | Body wall (ms) | 设备活动并集 (ms) | 内部空窗 (ms) |
| --- | ---: | ---: | ---: |
| 192K capture 首块 | 3221.954126 | 425.961623 | 2795.992503 |
| 256K capture 首块 | 426.426140 | 425.334521 | 1.091619 |

这些值来自原始 capture 的纳秒区间并集，不能把空窗删去后声称原始 Body 通过。
一个相同输入的单值预测也无法同时落在这两条观测的 ±10% 区间。
需要独立输入首次执行、图重放或编译缓存等状态，并确认等待归属，才能预测这部分差异。
仅有汇总 API 时间或客户端 SSE 到达时间不能恢复逐调用、逐 rank 的状态。

验收同时保留 capture 加权误差、主 population 误差和每个 population/chunk。
算子均值校准通过不代表每次原语调用、全部 Body 或独立泛化已经通过。

## A3 部署输入修正与尚未覆盖的服务边界

A3 `synth_qwen35_L8_E32_K2_tp8ep8_decode_256k_c1` 的历史模板使用
EP1、32 个本地专家和 64 维分片中间层；实际命令和 CSV 则是 EP8、
4 个本地专家、完整 512 维中间层，并有 MC2 Dispatch/Combine/AllGather。
`capture_policy.py` 现在导入命令中明确声明的 TP、DP 和 EP 开关，仅在
DP1、TP>1、启用 EP 且 MoE 拓扑受支持时推导 EP=TP，并替换继承的
`tp_join_reduce`。声明、推导、缺失字段和前后值分别记录；重复或动态参数
报错，显式不兼容 caller 保留并报告冲突。普通预测不要求采集证据。

对上述 EP1 模板修正，`capture_structure.py` 流式核对选定 CSV 中的
Dispatch/Combine、分组矩阵和 prepare 边界；只有受支持且一致的描述符才
绑定现有 MC2 TP slice caller。q1/q4 的完整图仍为 1/4 行，局部 prepare
按 `ceil(rows / TP) * TP` 扩到 8 行，再切成每 rank 1 行。已有 caller
保留，并用最终返回图核对；仅作用于 draft 的声明不能证明 Body caller
一致。版本化 routing/finalize 和 token permutation 等其他 caller 混入
窗口时拒绝绑定。混合或未覆盖 ABI 不变成成功匹配，读取、解析或预算错误
直接传播。

原生 GMM 的 16 行只表示分配容量，不能作为真实 routed token 数，也不要求
解析模型的工作行数与之相同。整份 E32 CSV 的 2,124 次 AllGather 不全部
归给 MoE；对账保留窗口计数和未归属边界。描述符一致不代表原生 kernel、
融合时序或二进制等价，peer window 与 group-list 值仍未观测。

`capture_ffn_guard.py` 比较修正前后实际生成的专家矩阵静态维度，只停用
适用范围已失效且缺少相应维度约束的 routed FFN 规则；无 CSV 的命令导入
也执行这一检查。其他响应及所有保留参数值不变，不增加耗时拟合或 Body
补偿。源路径、哈希和 CSV 行号只进入 provenance，不进入物理预测输入。

现有 `arch22_v2_caller` 能表达源拓扑的逻辑工作下界，但需要独立声明
peer window，本适配器不替它填默认值。此前四个未经校准的源拓扑情景为
2.6015–2.9036 ms，均低于实测 3.5675 ms；这些是历史反事实结果，不能
替代当前代码的全量回放，也不能把构图成功当作精度通过。

该 capture 的首个 AllReduce 平均 520.378 µs，其余调用平均 9.196 µs，
等待来源尚未识别，不能添加固定首层补偿。DSV4F 的真实 graph1 与 MC2
局部 pad8 也暴露了原生输出投影、SFA、MC2 欠算和其他算子高估；旧 graph8
曾用额外工作量抵消这些差异。两类失败继续计入完整验收分母。

## 尚未覆盖的 eager 调用与等待状态

Qwen3.5 q=64 的三个 eager capture 使用 ALLGATHER caller：DP=1、非 SP
条件下保留完整 64 行，按 EP 本地专家筛选，shared/routed 汇合后进行 TP
AllReduce。CSV 有 MoeInitRoutingV3/MoeFinalizeRoutingV2，没有 MC2
Dispatch/Combine。因此这些 capture 不套用上述 MC2 profile，但仍在全量分母中。
现有模板的 MC2 调用不能证明这条 eager 路径已被忠实建模。

39 个完整 forward 中，部分阶段具有较短 AllReduce 和较长内部空窗，后续阶段
则具有较长 AllReduce 和较短空窗。原始等待不能一律归为稳定传输服务或 host
固定开销。保留的 API 表只有累计时间/次数，没有 timestamp、thread 或关联 ID；
host AllReduce 计数为每 forward 90 次，而 target Body 原生调用为 80 次，
因此也不能把该表总时长直接加进每个 target Body。

## 捕获级 scope 与原生算子的共享集成

`scoped_native_replay.py` 为单个 capture 保存一次 prepared scope，并按每个实际
几何分别执行 C（`capture_scoped_structure` 的 caller 声明）再执行 B
（`prefill_native_observations` 的 FlashAttention/AllReduce 响应）。同一 capture
的 full q8064/context0 与 tail q256/context399744 各自保留自己的
`gather_output_materialization`（`per_rank_copy` 与 `view`），不会把某个窗口的
声明提升到整份 capture。观察值、forward 数、context 和计时边界都不改写；
prepare 只做一次，jobs materialise 后释放。

A5 截断 prefill 的 `context_offset` 仅在 forward 没有显式 context 时按
`requested_context - sum(query_rows)` 推导；显式观察到的 context 永不平移。
当权威 slim 证据显式给出 context/context_tokens、phase 或 sequences 时，必须与
prepared geometry 一致；不一致在定价前报错，绝不用 full scope 覆盖原分区。
缺失 capture/observation 是诚实的 `not_provided`/`unbound`，不冒充成功；
stale parser/config 的完整 extraction、超界读取和解析错误分别保留为
`stale`/显式失败/异常，不会被吞成“没有证据”。完整 extraction 的读取上限为
16 MiB，先做有界投影再做 JSON 解析，不保留 bulk 字段。

Wave5 当前入口在调用归档 evaluator 前运行 maintained per-capture driver：
复用归档 `extract_or_load` 的当前 parser/config 全量 observation，对每个
prefill forward 分别 C→B、计算最终物理 raw 的 cache key 并单独定价；归档
main 的 report/cohort 汇总仍由原脚本完成，scoped capture 的 prefill 结果按
path 替换。显式 scope plan 的 forward 数、每个 (tokens, context) 和签名必须与
观察分区完全一致，否则报错，不再静默回退到旧 `tpl_sig`。DSH 维护入口同样
按 capture 复用一次 prepared scope，并把每个几何的声明、native profile 与
最终 identity 记录在 sidecar。

`native_observations.PROFILE_FILES` 现在覆盖 C 的三个模块（含
`capture_scoped_geometry.py`）、B 的 adapter/builder/profile、共享 replay helper
和 DSH scoped driver，因此这些语义或数据变化会使 native identity 失效；
`pyproject.toml` 的 mindie-sim 依赖固定到
`dccea42b086fa5abd315c44dded188ed1e0347f8`。C 的生成图校验只把 Sim 实际产生的
`balanced_grouped_gate_up`/`balanced_grouped_down` 映射为同一语义 grouped 角色，
其余 recipe 名称不做前缀兜底；分组形状、专家 bank、hidden/intermediate 等物理维度
仍逐层核对，维度不一致继续拒绝。真实 A3 混合 fixture 的 full chunk 现在 C 与 B
同时 applied，A5 归档模板的继承 `alltoall` 在显式 `archive_template=True` 下替换为
`local_expert_reduce` 并 applied。`routing_basis` 只表达 raw 声明的
`declared_balanced_integer_ledger` 或 probability moments；四个历史 E48 capture 的
archived-template 继承来源记录在 handoff/capture provenance，不由 adapter 推断，
也不声称 native force-EPLB。仍有明确限制：A2 不在 scoped caller 适用域；
原生命令二进制、group-list 值、逐 forward 精度和独立泛化仍未证明；本适配器只选择
caller/native 物理响应，不做 Body 拟合或精度宣称。
