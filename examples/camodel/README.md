# CAModel 离线阶段成本导出

在算子开发阶段使用昇腾 CAModel 分析代表性 Kernel 与 Shape 后，可通过 `mindie-profiler camodel` 提取指定微流水阶段的净执行耗时：

```bash
mindie-profiler camodel \
  --trace /path/to/simulator/trace.json \
  --plan /path/to/stages.json \
  --output /tmp/camodel-durations.json
```

导出的 JSON 兼容保留的旧版 `mindie-sim pipeline --durations` 接口（当前新版 `mindie-sim` 已移除 `pipeline` 子命令，也不会将该阶段成本自动注入整网预测入口）。仅在配合旧版 `mindie-sim` 离线流水线推演时，才需运行以下命令（只读取导出的轻量阶段成本 JSON，不再调用 CAModel，也不依赖 `profiler`、CANN 或模拟器环境）：

```bash
mindie-sim pipeline \
  --graph /path/to/pipeline.json \
  --durations /tmp/camodel-durations.json
```

本目录下的 `trace.example.json` 与 `plan.example.json` 为手工构造的验证样例，并非真机或模拟器采集产物。按样例运行应输出 `load=1750 ns`、`compute=5000 ns`，可配合旧版 `mindie-sim` 仓库中的 `examples/camodel/pipeline.json` 验证。Trace 事件格式遵循 [PyPTO 的 CAModel Trace 清洗约定](https://github.com/hw-native-sys/pypto/blob/9f3ca53526bc31ccf7b7ec42064f4449f9db1acf/python/pypto/tools/clean_sim_trace.py)：指令事件使用 `ph="X"`，`pid` 标识物理核，`tid` 标识核内流水线（Pipe），同步原语还可能附带 `B`/`E` 事件。

## 阶段计划（`plan.json`）编写规范

以 `plan.example.json` 为模板，显式填写实际芯片 SKU、模拟器版本、Kernel 名称、Shape、Dtype、Tiling 参数与编译条件。阶段名称（Stage Name）应与目标流水线图中的节点名一致（也支持 `p0.load` 等带阶段前缀的节点命名）。

- **单核单流水线隔离**：每个阶段必须显式指定单一 `pid`、一组同属该物理流水线的 `tids`，以及若干次完整调用的时间窗口 `windows`（可选配精确的指令名列表 `names` 进行过滤）。窗口起止时间单位须与 Trace 保持一致。若清洗后的 Trace 含有 `MTE2#1` 等子通道，应将同一物理 Pipe 下的全部子通道一并填入 `tids`，但切勿将多个物理核或多个不同物理 Pipe 合并为同一个阶段。每个窗口必须完整覆盖一次阶段调用；不同迭代次数或不同流水阶段的调用应分开声明。
- **显式时间单位与时钟域**：`timestamp_unit` 为必填项，仅支持 `us`、`ns`，或附带 `clock_mhz` 的 `cycles`。Chrome Trace 中的 `displayTimeUnit="ns"` 仅影响前端展示，不能据此将 `ts`/`dur` 推定为纳秒。选用 `cycles` 时，`clock_mhz` 必须对应记录该计数器的实际时钟域；导出器不做跨时钟域换算或温控降频推断。
- **区间并集与同步指令剔除**：针对每次调用窗口，导出器计算选中指令时间区间的并集，自动剔除空闲间隙及 `SET_FLAG`、`WAIT_FLAG`、`BAR`、`BARRIER`、`PIPE_BARRIER` 等同步屏障原语，再对多次调用取中位数，并同时保留每次调用的净活跃时间（`active`）、指令累加耗时（`sum`）与首尾跨度（`span`）以便排查重叠。若窗口截断了指令、某次调用为空、同一条指令被重复划入两个阶段，或遇到不支持的事件格式，工具会直接报错退出，绝不输出残缺校准文件。导出前请确认 `ph="X"` 事件是否已剥离流水等待；若事件本身已包含等待耗时，切勿在图模型中重复叠加同类等待。阶段间的因果依赖仍由算子源码与流水线图定义，不从 Trace 时间顺序反推。

## 适用范围与验收边界

- **严格区分仿真与实测来源**：导出结果固定标记 `source_class="simulated"` 并附带完整筛选条件与上下文，仅作为开发期微架构阶段耗时输入，**不得**当作真机 `measured` / `observed` 样本写入校准库。旧版流水线工具显示的 `calibrated` 仅代表阶段耗时字段已填齐，不代表真机精度已验证通过；该输出也不会自动改变新版 `mindie-sim` 整网 `predict` 的算子成本。
- **留出集验证准则**：单核 CAModel 结果无法反映多核 HBM/L2 带宽争用、跨卡集合通信或服务级调度开销。接入前应先在同 Kernel、同 Shape 的真机训练点核对系统偏差，冻结映射规则后，再在独立留出集上对比接入前后的预测误差与配置排序；仅当留出集误差确有改善时方可报告精度收益。一旦修改 Kernel 实现、编译选项或核内流水结构，需重新采样并导出。
- **流式读取与资源上限**：工具复用流式 JSON 读取器逐事件扫描，默认最多保留 `200,000` 个选中区间、单次扫描超时 `30` 秒（超限即显式报错，可通过 `--max-intervals` 与 `--timeout-s` 调整）。工具不直接解析二进制 `visualize_data.bin`；如需分析该格式，请先使用对应 CANN 工具导出标准 Chrome Trace JSON。
