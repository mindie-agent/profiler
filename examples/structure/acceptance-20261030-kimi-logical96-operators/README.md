# Kimi logical96：完整 MatMul 契约回放

推荐入口为 [完整 canonical 记分牌](full-matrix-canonical/body-operator-family-scoreboard.md) 与 [JSON](full-matrix-canonical/body-operator-family-scoreboard.json)。顶层记分牌保留先完成的旧聚合一对一重定价，其后完整 MatMul ABI 分区恢复了新增角色；两臂共享原始观测，不能相加当独立采集。

固定 Sim `aeb66892a20588825e0eb443894d5d9b6b71c641`，12 个 A5 BF16 源、618 次完整 Body、3,348,783 个设备事件。完整 MatMul 443,106 次直方图逐值守恒。新增 logical96/global12/local，MLA Prolog/FIA 的物理16头padding与 BF16 router 的 FP32 输出独立声明。

canonical 严格评分事件由251,026增至314,746（+63,720），102/102 cohort通过：≤50us档98/98（单次绝对误差≤15us），>50us档4/4（相对误差≤15%）。未评分/条件参考族不在该分母内，不能宣称全部重算子已达标。新增12个router物理程序执行，78个矩阵cohort在相同runtime、相同physical key及work下复用本轮已执行成本；所有非矩阵family与成本逐项保留。MLA output可复用同合同的linear_output物理成本；q_a/output_gate仍是同工作量候选集合，实测一次只计一次，不宣称Host层级或两次调用。小batch物理padding导致不相同的合同继续保留未评分。

[960项独审](full-matrix-canonical/body-operator-family-independent-review.json)覆盖完整输入SHA/geometry/Body身份、逐族/全MatMul直方图、strict分母、新成本与复用成本、每次及活动误差算术。数据处理不重扫CSV；最终只增加输入身份验证和excluded计数修正，无候选、时长或成本变化，生成器pin时点已如实记录。

复现canonical：`reprice_kimi_matrix_partitions.py --previous <本目录/body-operator-family-scoreboard.json> --partition-dir ../acceptance-20261030-matrix-fix --output-dir <新目录>`。同运行时成本必须保持；工具拒绝跨runtime复用。

`native-partitions/` 为后续6族工作中的4类缺证据补档：RecurrentKda、CausalConv1d、AttnResFwd、MlaPrologV3共215,682事件、372完整ABI×整体层拓扑桶，618 Body窗口和已归档全hist完全一致。12源分别定向流扫一次，共178.292秒、峰212.4MiB。DispatchV3/CombineV3已有全ABI，无需重复扫描。补档只补证据；其条件资源成本将另立明确参考臂，不计入本canonical严格通过率。
