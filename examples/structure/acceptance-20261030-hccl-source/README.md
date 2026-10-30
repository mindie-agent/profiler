# A3 / A5 HCCL 展开模式与源码 Template 账本

本账本固定公开源码 `c2d6790464654ccf58aca39448de4b65fdc7b184`，只读本地已有采集与源码，不执行采集、不修改 Sim。源码 revision 与采集容器内 HCCL 二进制的对应关系尚未建立；因此“源码允许的候选”与“实测选中的 Template”分开保存。

辅助知识卡 [executor-selector.md](</Users/maoxx241/code/refs/cannbot-skills/communication/hccl-aicpu-best-practice/references/executor-selector.md>) 与 [source-baseline.json](</Users/maoxx241/code/refs/cannbot-skills/communication/hccl-aicpu-best-practice/references/source-baseline.json>) 包含 `88a…` / `978d…` / `a9b…` 等不同 revision，本次只用来导航。实际规则以本账本固定的 `c2d679…` 源码、文件 SHA 与行号为准，不能将旧知识卡的 `HCCL_USE_NEW_SELECTOR` 开关直接用于解释当前采集。

当前完整关联 **66 份采集、5,250 个已验收 Body、222 个实际 geometry**。完整 capture 保留 784 个原始签名分组，Body 内保留 3,628 个分组；两套范围不能累加。原 9 份 A5 的主几何 HCOM 逐 duration histogram 与早期结果完全一致。本工具只读取已验收元数据，不重复解析 CSV。

| 已声明硬件 | 来源数 | Body 数 | 实际 geometry | AIV collective device calls | AICPU controller calls | HCOM envelope calls | 融合通信程序 calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A3 `Ascend910_9362` | 30 | 2,894 | 124 | 23,892 | 226,480 | 226,678 | 112,704 |
| A5 `Ascend950DT_9582` | 36 | 2,356 | 98 | 55,312 | 36,424 | 289,563 | 214,584 |

这些是分离的证据人口，不能横向相加成通信调用或墙钟时间。尤其 **A3 也观测到 AIV collective tasks**，不能将 A3 全部归为 AICPU。已保留的通信名称/core 过滤范围内，未识别可确认的 CCU_MS / CCU_SCHED / CCU / SDMA / Notify 执行单元；这不是全部执行单元的穷尽 census。尤其旧 collector 没有单独 DPU 名称/core 分支，仅可能经 hcom/COMMUNICATION 捕获 DPU 相关行，因此 DPU 明确标为 `unknown_due_to_capture_filter_scope`，不能称为本批完整 CSV 中不存在。即便某类签名未观测，也不证明内部从未执行该机制。融合 MC2 的 AIV/MIX_AIV 执行单元也不等于一个独立 HCCL 算法。

同源旧 Kimi p32k 的 `k3lc-os1.tgz` 已有完整保留 trace，源 CSV member SHA 与当前源精确相同。该 trace 的 425,826 个事件中 425,759 是 Python function、64 metadata、1 Trace、2 instant；没有 NPU task/stream/correlation、flow 或算法字段。账本明确写 `existing_trace_but_no_device_correlation`，并非“没有 trace”。相邻 communication_statistic 只有 Count/Total/Min/Avg/Max/Ratio，不能生成 payload 或模板证据。[关联资产核验](../acceptance-20261030-hccl-66/associated-artifacts.json)

因此当前可以确认 514 个 Body 分组的 AIV collective engine，以及 1,259 个分组的 AICPU controller；具体 runtime Template 的 confirmed 数仍为 0。所有适用的公开源码候选、缺失参数与源码文件身份都已列明，并未把这些采集整体归为不可分析。


## 两个阈值不能当成全平台规则

这份源码的实际入口先计算 rank graph。`level0Topo == MESH_1D` **或** `IsDevType960()` 时调用 `SelectorEngine`，其流程是过滤候选、计算 cost table、处理 tuner、选择最小成本；其他路径才进入旧 `ExecuteSelector`。所以即使消息量小于 128 KiB，也不能直接把当前 MESH_1D 采集绑定成 OneShot。[入口](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/op_common.cc:174>)、[成本表选路](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/selector/selector_engine.cc:272>)

| 源码条件 | 精确阈值与作用 | 适用边界 |
| --- | --- | --- |
| AIV AllReduce 旧 helper；MESH_1D；通信域 rank 数 ≤8 | `dataSize < 128*1024` 选 OneShot；等于阈值选 TwoShot | 不是 AllGather/ReduceScatter 阈值，更不是引擎选择阈值 |
| 同 helper；MESH_1D；rank 数 >8 | `<512*1024` 为小数据 | 仍需通过拓扑、dtype、reduce-op、CCL buffer 等前置条件 |
| 同 helper；level0 不是 MESH_1D | 直接 TwoShot | 不能把 A3/A5 品牌替代 rank graph |
| AICPU AllReduce 单层 mesh 旧 helper | `dataSize <= 8*1024*1024` OneShot | 64-bit dtype/PROD 有专门分支；两级网络下 rank=2 且 ≥8MiB detour 优先 |
| 普通 AICPU AllReduce 更大消息 | `dataSize * (8/rank/rank) >32MiB` 才进入 ChunkTwoShot/Concur 分支 | 源码是 `8/rank/rank`，不是 `(8/rank)^2`；后者出现在 ReduceScatter 中 |
| AIV 常规大数据 guard | AR 检查 full-input bytes；AG/RS 检查 `count*dtype_size*rank` | `AIV_ONLY` 可跳过其中的普通大小 guard，但不能跳过所有 buffer/合法性检查 |

精确比较符、前置 return 与分支优先级见 [AIV AllReduce](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/selector/all_reduce_auto_selector.cc:604>)、[AICPU AllReduce](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/selector/all_reduce_auto_selector.cc:530>)、[公共 8MiB 常量](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/selector/auto_selector_base.h:23>)。AIV legacy helper 排除 PROD、UINT64/FP64、部分保序、多级及 UB-RTP 条件；成本表路径的 `REGISTER_ALG_ATTRS` 又有自己的 eligibility，二者不能混用。[注册约束](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/algorithm/executor/ins_v2_all_reduce_sole_executor.cc:438>)

## payload 的量纲必须先统一

| Collective | `DataDes.count` | `count * dtype_size` | 完整输入 / 输出 |
| --- | --- | --- | --- |
| AllReduce | 每 rank 完整 count | 每 rank 的完整数据量 | input=output=dataSize |
| AllGather | 每 rank sendCount | 本 rank 输入 shard | input=dataSize；output=dataSize×rank |
| ReduceScatter | 每 rank recvCount | 本 rank 输出 shard | input=dataSize×rank；output=dataSize |
| AllToAllV / VC | 不能用一个标量替代 | 需要真实 count/displacement 矩阵和 send/recv dtype | 留待完整调用参数，不能从邻近矩阵输出猜测 |

来源为 [AllReduce 参数构造](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/all_reduce.cc:164>)、[AllGather 参数构造](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_gather/all_gather.cc:158>)、[ReduceScatter 参数构造](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/reduce_scatter/reduce_scatter.cc:154>)。Profiler 中前置张量的 `M×H×dtype` 和 Sim 的 declared link bytes 保留为条件证据；本批通信行无实际 payload 字段，`measured_payload_bytes` 保持 null。

## A3 / A5 拓扑与模式证据

`TWO_DIE_REGULAR` 是源码根据通信域 **endpoint 的 die-link 分布**派生的类型：仅 MESH_1D 且 rank>2，两个 die 都有 link，并且计数相差 1，才归此类。A3 一机 8 卡 16 Die 并不自动证明某个 TP 子通信域满足这个条件；rank≤2 在此函数中直接归 SINGLE_DIE。[派生函数](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/topo_info/topo_host.cc:1179>)

`MESH_1D`、`MESH_1D_CLOS`、`CLOS` 是 rank graph 形态；`topLevelUboe` 则读取最高网络层 link protocol，不等同“跨主机”或“A5”。顶层 UBOE 可以使普通模式优先 AICPU，且对多级 pipeline/NHR 分支有直接影响。[UBOE 判断](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/topo_info/topo_host.cc:686>)、[入口引擎覆盖](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/op_common.cc:174>)、[多级 AllReduce](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/selector/all_reduce_auto_selector.cc:437>)

模式还受版本与通信域配置影响：该 revision 对 A5 及后续、且 `HcclConfigGetInfo` 可用时，使用 communicator 的 expansion mode；较早设备或缺少接口时，保留环境变量覆盖顺序。不能把一个 launch script 中的 `HCCL_OP_EXPANSION_MODE` 当成所有 rank 已生效的模式，更不能把 AIV fallback 列表当成实际发生过的 fallback。[模式解析](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/op_common.cc:3668>)、[引擎候选优先级](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/selector/selector_engine.cc:69>)

## Template 与可用物理机制

JSON 按真实宏提取了 **201/201 条注册**：95 单模板、27 MULTI、49 双模板、20 四模板、5 executor-only、4 无 topomatch 单模板与 1 topology-only。保存每条 `algorithm_name → executor_class → 有序 template 数组` 与源文件 SHA/行号；多模板中重复的层间阶段保持原次序，不能压成一个 template 或丢掉重复阶段。注册表不是运行时兼容性白名单；构建条件、rank graph、op 属性、覆盖配置与 tuner 仍可能排除候选。

- AIV AllReduce 实测 `AivKernel` 可确认执行引擎，公开源码候选为 `AivTempAllReduceMesh1DOneShot` / `AivTempAllReduceMesh1DTwoShot`。名字里没有 one/two-shot，因此不在二者间虚构绑定。
- AICPU Mesh OneShot 与 TwoShot 对应独立模板。TwoShot 明确执行 ReduceScatter 再 AllGather；OneShot 具有不同传输、local-copy/reduce、同步及 launch 项。Sim 应按这些阶段建立资源工作，保留原始真实通信 elapsed 可能含 peer wait 的边界。[注册](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/algorithm/executor/ins_v2_all_reduce_sole_executor.cc:371>)、[TwoShot 执行阶段](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/algorithm/template/aicpu/ins_temp_all_reduce_mesh_1D_two_shot.cc:164>)
- 成本表不是“总字节/单链路带宽”。它按网络段计算 `(A/util+B)*dataSize+C`、组内 MAX 或 SUM、组间累加，再与 launch 项 D 比较。OneShot/TwoShot 的 rank、端口、本地复制、规约与同步项不同。[成本公式](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/op_common/selector/cost_table.cc:366>)、[OneShot 系数](</Volumes/data-tmp/tmp/sim-hccl-source-20261030/src/ops/all_reduce/algorithm/template/aicpu/ins_temp_all_reduce_mesh_1D_one_shot.cc:23>)
- `HcclLaunchAicpuKernel`、`reduce_scatterAicpuKernel` 的 AI_CPU 属性只确认控制任务执行。没有 parent-child/correlation 证据时，不把它的 elapsed 加到 HCOM/device-task 上，也不据此反推 Ring/NHR/mesh。完整 task locator 与重复 Task ID 的事实继续保留。

## 与 66-source 真实账本的接口

`audit_hccl_source_routes.py` 同时接收旧 `mindie-retained-body-hccl-ledger/1` 与新 `mindie-capture-and-body-hccl-ledger/1`。新格式保留完整 capture 的 phase-unclassified inventory、每个已验收 Body geometry 的人口，以及 underscore controller alias overlay；不把 capture 与 Body 计数相加、不修改已验收时长。每条分类带原始 JSON pointer，可回到完整 histogram/PMU/locator。相同源 SHA 不能以旧 9 与新 66 两份重复计入。输出分三层：

1. `observed_engine`：device engine 与 controller engine 分开，证据仅来自实际记录。
2. `candidate_algorithm_names` / `candidate_template_classes`：固定源码注册域中的有限候选，附全部文件/行号；`template_selection_confirmed=false`。
3. `missing_selection_evidence`：具体缺失的 communicator members/rank size、rank graph、payload count/dtype/reduce-op、有效 expansion mode、HCCL_ALGO、tuner/plugin、CCL buffer、determinism 等。拿到真实 selected-algo 日志或等价调用证据后才能升级为确定模板。

实际执行单元分别保留 AIV、AICPU、CCU_MS、CCU_SCHED、未知子模式的 CCU、DPU、SDMA、Notify、MIX_AIV；只有 `CcuKernel` 时不会强分 MS/SCHED，SDMA/Notify 不等于集合算法引擎。缺少签名仅表示本采集未观测到，不证明运行机制不存在。`MoeDistribute*` 等融合通信程序独立列出，不匹配普通 HCCL executor 注册域、不与 HCOM 累计相加。AllGatherV / ReduceScatterV / AllToAllVC 与固定 count 算子分开。

七项测试覆盖 AR/AG/RS 字节定义、128KiB/8MiB 精确边界与 cost-model 路由、two-die 派生规则、真实 AIV 记录不能借前置张量强绑 OneShot，以及真实 variable collective / fused program / controller alias 边界和旧账本人口保持及带逗号注释的真实多模板注册解析。7 tests passed，零 raw capture 重扫，零 Sim 成本计算。

复现只消费已落盘的 ledger：

```sh
python3 examples/structure/audit_hccl_source_routes.py \
  --source-root /Volumes/data-tmp/tmp/sim-hccl-source-20261030 \
  --associated-artifacts examples/structure/acceptance-20261030-hccl-66/associated-artifacts.json \
  --output examples/structure/acceptance-20261030-hccl-source/hccl-source-template-audit.json \
  $(for p in examples/structure/acceptance-20261030-hccl-66/*-capture-hccl.json; do printf -- '--ledger %s ' "$p"; done)
```

全量 join 基准为 2.40 秒、峰值约 195 MiB；零 raw capture 解析、零 Sim 成本计算。源码注册表包含编译条件下的候选域，不能作为当前捕获二进制的兼容性保证。

独立审核完成 80,492 项检查（448 项源码文件 SHA/行边界，80,044 项 66-source/geometry/分组人口与候选域核对），0 失败。随后仅补充执行单元过滤范围说明，全部源码、注册、case 分组和数值逐项相同。DPU 额外只读旁证在 [统计元数据检查](../acceptance-20261030-hccl-66/dpu-presence-metadata.json)：60 个来源、374 份统计文件、32,126 行未命中 DPU，另 6 个来源没有该统计；这仍不能消除原 event-filter 的范围限制。
