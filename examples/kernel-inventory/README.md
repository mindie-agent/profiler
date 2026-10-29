# 复用已有 profiling 的 kernel / shape 变体

```bash
python -m mindie_profiler kernels --manifest sources.json --output-dir /path/to/reuse
```

`sources.json` 声明只读的数据根目录与上下文，例如：

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

硬件、软件和场景信息复用生产方已有记录，不能只凭目录名猜 SKU。不同
环境、设备、采集窗口和请求 cell 分开；不把相同张量池 shape 下的不同
有效 KV 长度、不同并发负载混成一个独占算子曲线。前缀较长的上下文覆盖
较短的前缀。已有 train/heldout 标签应直接保留；未声明的保留 unassigned。

输入支持原位 CSV、gzip CSV，以及 tar.gz/tgz 内的 kernel_details/op_summary。
只有 task_time 导出时也保留其中的观测与缺字段；同目录已有完整导出则优先
复用完整记录，不再重复计入 task_time。
整份 trace 不进内存，解包也不落盘。计时使用原始十进制时间戳转换为 ns。
同一事件的复制件和重复导入只保留一次，原始文件不修改。发生读取错误或
源文件变更时明确记录失败，不把部分源当完整数据；已有成功源可增量复用。

输出：

- `kernels.sqlite`：每个捕获事件、完整输入/输出签名、采集上下文和时长统计。
- `variants.jsonl`：完整变体清单，含调用次数、median/mean/min/max。
- `missing.jsonl`：缺字段、未知环境、heldout 或应走通信模型的条目。
- `summary.json`：数据量、去重数、失败及已有校准资产引用。

shape、dtype、format 保留全部输入和输出参数及可选参数槽位，不只取第一个
张量。没有记录输入值/tiling 的信息不会凭空补全。统计量为同一捕获条件下
事件时长的中位数，不冒充独立 trial 的统计量，也不把 busy duration 当墙钟
占比。通信、AICPU 的信息仍在清单中，其完整成本继续交给既有拓扑模型。

## 接入 mindie-sim

新版 `sim` 已有只读 `ProfilerCatalogue` 接口，可以检查此 DB 中的变体和
来源样本：

```python
from mindie_sim.observations.store import ProfilerCatalogue

with ProfilerCatalogue("/path/to/reuse/kernels.sqlite") as catalogue:
    for variant in catalogue.variants(limit=10):
        print(variant)
        print(list(catalogue.samples(variant["id"], limit=3)))
```

该接口只读取观测，不会把 median 自动替换成预测成本；当前没有接通
`profiled_kernels` provider 或整网预测的自动成本注入。模型结构与实测的
比较使用 profiler 的显式结构契约和 cohort 比较路径，见主 README。

后续接入观测成本还需显式绑定完整执行条件、lowering 和计时边界，并避免
重复计入整 kernel 的计算/HBM 耗时。仅有捕获时长不能推断新的竞争条件、
跨流重叠或独占服务成本。`heldout` 条目不提供校准成本；`unassigned`
也不代表训练或独立预测精度通过。已有校准、通信模型和 DSH 验收不因本清单改变。

## 补齐顺序

先复用已有的专用校准和原始记录，再补已有 DB/Host 日志/框架源码中的关联
字段。需核内分解时，准备实际 kernel binary、tiling 和输入状态，使用
CAModel 离线分析；模拟结果保留 simulated 来源。只有这些途径均无法解决
的实测缺口，才交由原来的 coordinator 排队补采，不抢占当前 DSH 租约。
