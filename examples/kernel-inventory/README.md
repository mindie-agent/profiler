# 从存量 Profiling 产物构建 Kernel / Shape 变体清单

通过 `mindie-profiler kernels` 子命令，可在不解压落盘、不修改原始采集文件的前提下，流式扫描存量 Profiling 目录并构建跨运行去重的算子与张量变体目录：

```bash
python -m mindie_profiler kernels \
  --manifest sources.json \
  --output-dir /path/to/reuse
```

`sources.json` 用于声明只读采集根目录与对应的硬件/软件上下文，例如：

```json
{
  "roots": ["/path/to/captured-data"],
  "contexts": [{
    "prefix": "/path/to/captured-data/run-a",
    "context": {
      "hardware_key": "Ascend910_9362",
      "environment_key": "the-declared-image-and-stack",
      "capture_group": "the-original-run",
      "source_reports": ["/path/to/capture-report.md"],
      "split": "unassigned"
    }
  }]
}
```

## 上下文声明与流式扫描规则

- **显式上下文隔离（禁猜硬件 SKU）**：硬件型号、软件栈与采集分组必须复用生产侧真实记录，不单凭目录名猜测芯片 SKU。不同软件环境、设备型号、采集窗口与压测单元（Cell）严格分开建档；即使物理张量池 Shape 相同，不同有效 KV 长度或不同并发负载下的样本也不混并成单一独占算子曲线。当多条 `prefix` 同时命中时，最长路径前缀优先；已有的 `train` / `heldout` 数据集划分标签原样保留，未声明条目记为 `unassigned`。
- **多格式原位流式读取**：支持直接扫描原始 CSV、`.csv.gz` 以及 `.tar.gz` / `.tgz` 归档包内的 `kernel_details.csv` 与 `op_summary.csv`。若目录仅含 `task_time` 导出，工具会保留其耗时观测并如实记录缺失字段；若同目录已存在完整 Kernel 导出，则优先采用完整导出，绝不与 `task_time` 重复计入。整个扫描过程不将整份 Trace 载入内存，归档包也不解压落盘；时间戳直接从原始十进制文本精确换算为整数纳秒。同一事件的副本或重复导入仅保留一份。读取异常或源文件在扫描期间发生变更时均显式记录失败，绝不将残缺源伪装为完整采集；此前已成功入库的源支持增量复用。

## 输出产物与统计口径

运行完成后在 `--output-dir` 下生成四份产物：

- `kernels.sqlite`：逐次捕获事件明细、完整输入/输出张量签名、采集上下文与耗时分布统计。
- `variants.jsonl`：去重后的算子变体总表，包含调用次数及单次耗时 `median` / `mean` / `min` / `max`。
- `missing.jsonl`：缺失关键字段、环境未知、标记为 `heldout` 或应交由通信模型处理的算子条目。
- `summary.json`：扫描总量、去重计数、失败明细及关联校准资产摘要。

张量签名完整保留全部输入、输出及可选参数槽位的 `shape`、`dtype` 与 `format`，而非仅截取首个输入张量；原始产物的未记录标量值或 Tiling 参数不做凭空补全。表中 `median` 仅代表同一采集条件下重复调用耗时的样本中位数，不等同于多次独立实验（Trial）的统计分布，也不将单算子净耗时直接折算为整步墙钟占比。HCCL 通信与 AICPU 算子同样记录在册，但其端到端耗时仍由对应拓扑与控制面模型负责建模。

## 在 `mindie-sim` 中只读检索

配套的 `mindie-sim` 提供只读 `ProfilerCatalogue` 接口，可用于检索 `kernels.sqlite` 中的算子变体与原始样本：

```python
from mindie_sim.observations.store import ProfilerCatalogue

with ProfilerCatalogue("/path/to/reuse/kernels.sqlite") as catalogue:
    for variant in catalogue.variants(limit=10):
        print(variant)
        print(list(catalogue.samples(variant["id"], limit=3)))
```

该接口仅用于只读查询实测样本，不会将变体中位数自动注入 `profiled_kernels` 提供方或整网预测成本路径。模型声明结构与实测窗口的对账请使用主 [`README.md`](../../README.md) 中介绍的显式结构映射与同构算子群（Cohort）比较流程。

若后续将实测算子耗时用于局部校准，仍需显式绑定完整执行条件、图下沉（Lowering）形态与计时边界，避免与整图计算/HBM 访存模型重复计费。仅凭单次采集耗时无法外推新的资源争用、多流重叠或独占服务耗时；标记为 `heldout` 的样本严禁用于参数拟合，`unassigned` 样本亦不代表已通过独立泛化验证。既有校准参数、通信模型与独立留出验收结论均不因构建本目录而改变。

## 实测缺口补齐优先级

排查未知算子变体缺口时，建议按以下顺序推进：

1. 优先复用存量专项校准记录与已归档的原始采集文件；
2. 从同批次 SQLite DB、Host 启动日志与推理框架源码中补齐关联上下文与参数槽位；
3. 需要拆解核内微流水线时，准备实际算子二进制、Tiling 参数与输入状态，通过 [`CAModel 离线导出`](../camodel/README.md) 分析（结果保留 `simulated` 标记）；
4. 仅当上述离线途径均无法覆盖真实硬件缺口时，再提交集群统一调度队列排期补采，不在只读编目流程中抢占在线推理或基准测试租约。
