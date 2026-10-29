# Kimi：17 份已有采集的 Decode 主体提取

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

`decode-forward-09811dad-replay.json/.md` 独立记录 17 次新成本执行，固定运行时 228 个文件的 SHA。主桶覆盖 1769/1799 个主体，其余 14 桶明确延后预测。A3 四层模型 5/5 个主体工况通过 ±15%；A5 BF16 93 层模型 12 个主体工况仍低估约 23%–30%。四层结果不能外推完整 93 层模型，且本批也不能与旧 FP8 / DP4 的 Kimi 采集混为一个 checkpoint。
