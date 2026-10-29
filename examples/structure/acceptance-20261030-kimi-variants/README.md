# Kimi：17 份已有采集的 Decode 主体提取

**成本验收已撤销：** `prediction-input-binding-invalidation.json` 记录 Sim `09811dad` 忽略外层量化声明的证据。A5 BF16 与 A3 W4A8 均错误解析为 `mxfp4_routed_only`；该版本的 17 份成本结果和未完成的算子回放都不得计入准确率。原始 JSON 数值与 SHA 保留为失效诊断，1799 个实测主体仍有效。

主体提取只读取本地已有采集，没有启动真机任务。独立成本回放使用 Sim `09811dad` 源码，与提取回执分别保存。

- A5：12 份 TP8 / DP1 / EP8、expert16/top8 BF16 条件声明，93 个主体层；请求并发 1/2/4/8/16/32，实际初始 prompt 为 4104 或 16392 tokens。
- A3：5 份 TP8 / DP1 / EP8 W4A8 四层模型，3 KDA + 1 MLA；这是缩小层数的模型，不能冒充完整 93 层耗时。

Sim 提供层序列和声明。设备张量锚确定完整层序列、执行 batch 和 q；这些是结构引导关联，不是 Host/module 实例绑定。FFN 中间物理 padding 不替代主体 query rows。每个 Forward 的完整主体、Layer0、逐层跨度、设备事件覆盖区间与内部未覆盖间隙分别保留；真实通信等待没有从主体扣除。

17 份源均有非零结果：1799 个完整主体、31 个执行几何桶，各源主桶合计覆盖 1769 个主体。所有桶的 q=1，B 来自对应 attention block table。客户端 TPOT 独立保留，prompt 长度仅可作为后续预测的条件初始上下文，不代表逐步已知 KV 长度。完整配置与 checkpoint 文件仍缺少的证据列在 manifest，未将启动意图当作已证明的实际均衡。

第一轮在完成 14 份源后被主动中断：A3 缺少 `DequantSituQuant` 激活识别，A5 MLA31 的 block-table selector 回归导致 B/q 未解析。`initial-diagnostic-attempt.json` 保存实际失败尝试与分母，不算成功验收。修复后统一重扫 17 份源；最终 receipt 同时固定 segmentation 与 attention-contract helper 的 SHA。没有把重扫当作新增采集。

复现命令（仓库根目录，使用已安装 Sim 依赖的 Python）：

```sh
PYTHONPATH=/Users/maoxx241/code/sim-rewrite-20261027:/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/build_kimi_decode_cases.py \
  --case-dir /Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/kimi-variants
PYTHONPATH=/Users/maoxx241/code/sim-rewrite-20261027:/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_decode_auto_evidence.py \
  --manifest examples/structure/acceptance-20261030-kimi-variants/decode-forward-auto-cases.json \
  --output examples/structure/acceptance-20261030-kimi-variants
```

`decode-forward-auto-acceptance.json` 是完整提取回执，`decode-geometry-priority.json` 保留全部几何桶及分母；Markdown 表格仅展示各源优先桶。

`decode-forward-09811dad-replay.json/.md` 保留 17 次实际执行的历史诊断，固定运行时 228 个文件的 SHA。主桶覆盖 1769/1799 个实测主体，其余 14 桶明确延后预测。旧报告中的通过率及低估幅度均因上述输入绑定错误失效，需要修复后的新成本执行才能重新验收。四层结果不能外推完整 93 层模型，本批也不能与旧 FP8 / DP4 采集混为一个 checkpoint。

修复后的正式结果是 `decode-forward-332f0420-window8-replay.json/.md`：17 次新执行使用正确解析的 W4A8 / BF16 和用户指定的有限 peer window=8，每份预测直接保存 `model_representation.quant`。有效结果为 1/17 个主体工况通过、12/1136 层通过；A3 c64 误差为 −7.19%，A3 c32 的 −15.53% 仍严格判失败。所有未通过值继续保留，不能继承失效报告的 5/5 结论。

`decode-forward-332f0420-serial-control-replay.json/.md` 在同一修复运行时保留原 caller，比较 A5 p4k 的 c1/c16/c32 三档。串行控制预测分别为 25.671598/28.766833/32.725385 ms，window8 正式臂分别为 23.684398/26.779633/30.738185 ms，每档减少 1.9872 ms。这个对照可隔离 caller window 的影响；与旧 09811 的直接比较同时包含运行时和量化解析变化。三个原声明的相同字节另保存在 `declarations/serial-control/`，SHA 与原执行 manifest 一致；原执行路径和回执没有被重写。
