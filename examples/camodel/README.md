# CAModel 离线阶段成本导出

开发时用 CAModel 分析代表性的 kernel/shape，再导出选定阶段的时长。
输出兼容保留的旧版 `mindie-sim pipeline --durations` 接口；新版 sim
没有这个 pipeline CLI，也没有自动导入这些阶段成本的预测入口。

```bash
mindie-profiler camodel --trace /path/to/simulator/trace.json \
  --plan /path/to/stages.json --output /tmp/camodel-durations.json
```

只有使用保留的旧版 sim 时，才运行以下命令。它读取小型阶段成本文件，
不再运行 CAModel，也不要求安装 profiler、CANN 或模拟器：

```bash
mindie-sim pipeline --graph /path/to/pipeline.json \
  --durations /tmp/camodel-durations.json
```

这里的 `trace.example.json` 和 `plan.example.json` 是明确声明的算法例子，
不是实机或模拟器采集记录。运行它们应得到 `load=1750 ns`、
`compute=5000 ns`，可配合旧版 sim 仓库的 `examples/camodel/pipeline.json` 使用。
事件布局依据 [PyPTO 的 CAModel trace 读取实现](https://github.com/hw-native-sys/pypto/blob/9f3ca53526bc31ccf7b7ec42064f4449f9db1acf/python/pypto/tools/clean_sim_trace.py)：
指令为 `ph=X`，`pid` 标识核，`tid` 标识流水线；同步还可能使用 B/E 事件。

## 选择实际阶段

以 `plan.example.json` 为模板，填写实际的芯片 SKU、模拟器版本、kernel、
shape、dtype、tiling 和编译条件。阶段名称对应已有 pipeline graph 的名称，
也可以使用 `p0.load` 等 phase-qualified node 名称。

每个阶段显式指定一个 `pid`、一组 `tids`，以及一组完整 invocation 的
`windows`；可用精确的 `names` 过滤指令。窗口边界与 trace 使用同一单位。
清洗后的 trace 若有 `MTE2#1` 等子车道，把同一物理 pipe 的子车道全部列入
`tids`。不要把多个物理核或多个 pipe 合成一个阶段。每个窗口必须对应一次
完整阶段执行；不同次数或不同 phase 的调用应分别声明。

`timestamp_unit` 必填：`us`、`ns`，或带 `clock_mhz` 的 `cycles`。
Chrome trace 的 `displayTimeUnit=ns` 仅控制显示，不能据此把 `ts`/`dur`
解释为 ns。选择 cycles 时，频率必须对应这些 tick 的时钟域；导出不做
跨时钟域或热态频率推断。

对每次 invocation，导出选中指令时间区间的并集，排除空闲间隙及
SET_FLAG/WAIT_FLAG/BAR/BARRIER/PIPE_BARRIER，然后对 invocation 取中位数。
保留每次的 active time、指令累计时间及完整 span，以便检查重叠。
截断指令的窗口、空 invocation、重复分配到两个阶段的指令及不支持的
指令事件格式均明确报错；不会输出不完整校准。先确认 `X` 事件表示的
时间范围适合目标阶段；如果包含未分离的等待，不能把它当作独立服务时长
再重复叠加相同等待。依赖关系仍由源码和 graph 给出，不从 trace 顺序推断。

## 使用与验收边界

输出标注 `source_class=simulated`、完整选择条件和上下文。它是开发期的
仿真成本输入，不作为真机 `measured/observed` 样本写入校准库。
旧版 pipeline 的 `calibrated` 只表示阶段时长输入齐全，不代表真机精度
达标。该兼容输出没有把结果自动注入新版 sim 或整网 `predict` 的算子
成本路径。

单核结果不能直接代表多核 HBM/L2 竞争、通信或服务调度。先对同 kernel、
同 shape 的真机训练点检查偏差，再冻结规则，用独立留出集比较接入前后的
预测误差和配置排序；只有实际改善才能报告精度提升。改变 kernel、编译条件
或流水结构时，应重新选择采样并导出。

原始 JSON 用已有流式 reader 逐事件读取；默认最多保留 200,000 个选中
区间、扫描 30 秒。超限报错，可用 `--max-intervals`、`--timeout-s` 调整。
不读取 `visualize_data.bin`；需要时使用对应 CANN 工具导出 Chrome trace。
