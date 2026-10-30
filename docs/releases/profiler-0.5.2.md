# mindie-profiler 0.5.2

本版本交付 Decode 结构拆解、实测事件关联与统一验证管线，并保留 0.5.1 的 CLI 帮助和错误诊断修复。

- CSV/DB/trace 统一事件及张量契约解析，复用 Sim 声明的结构、融合子图和物理资源边界。支持 Attention、cache、GDN/KDA、MoE、mHC、残差及融合算子。
- 从真实 kernel CSV 自动识别完整 Decode Body 和层级边界，分别输出设备活动并集、内部未覆盖区间、外围模型阶段与 AICPU 控制等待。
- 同构 cohort 按完整契约和物理工作量对账；图模式下没有层级证据时不猜测具体层。单次调用 >50 us 使用 15% 相对误差，<=50 us 使用 15 us 绝对容差。
- 唯一 `pipeline.py`、`cases.json` 和 `results/` 替代日期/commit 过程目录和一次性脚本。每轮使用一个 Sim 包重新预测，逐源完整结果以 SHA256 外置，入库 JSON 小于 5 MB。
- 服务域拟合明确保留训练与留出源集合、实际实现/精度/布局/执行边界和物理坐标。跨 TP/并发不直接复制单点耗时；同源校准成绩不代表盲测泛化。
- Prefill 和 Engine 使用同一入口。Prefill 比较完整 chunk 的 Body；客户端 TTFT、设备周期、MTP/外围区间与 completion-token TPOT 保留各自边界。Serving 契约未满足或预测超时均显式报告，不生成假 PASS。

当前实测结果见源码 `examples/structure/results/`。所有硬件证据来自既有 A3/A5 采集的离线回放，本轮未启动设备任务。原始捕获和外部完整证据不包含在发行包中。

结构与成本对账要求配套 Sim 0.8.0；发布依赖锁定其正式发行提交。发行附件的 benchmark 报告记录精确标签、干净源码、测试结果和实际测量。精度达标、程序执行成功与证据完备是分别报告的状态。
