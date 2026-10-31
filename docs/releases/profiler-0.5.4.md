# mindie-profiler 0.5.4

本版本配套 `mindie-sim 0.8.2`，完成全量注册 Decode（280 case）与 Prefill（15 case）100% 压入 `<= 10%` 相对误差，并将全舰队 DSH 870 个实测捕获（含 575 个未注册留出集案例）收敛至 `99.77% <= 10%`（`0` 未解析案例）。

- **注册 Decode 与 Prefill 全量 100% 收敛至 `<= 10%`**：
  - `examples/structure/results/decode.md`：**280/280（100.00%）误差 `<= 10.0%`**（最大绝对相对误差 `9.89%`，平均绝对相对误差 `3.36%`，中位数 `2.72%`），通过高并发 MoE 调度与通信长尾校准将此前 `10.33%–14.58%` 的 27 个边际案例全部压入 `<= 10%`，并在 `cases.json` 与对应 case 文件中同步更新 `in_sample` 溯源与证据哈希；
  - `examples/structure/results/prefill.md`：**15/15（100.00%）可比 Prefill Body 案例误差 `<= 8.42%`**（平均绝对相对误差 `4.01%`，中位数 `4.07%`）。
- **双流 MoE 通信边界识别与 DSH 全舰队 870 捕获 `99.77% <= 10%` 泛化收敛**：
  - `mindie_profiler/communication_bounds.py` 与 `mindie_profiler/decode_segmentation.py`：新增 `dual_stream_moe_hidden_consumer` 双流 MoE 隐藏消费者边界识别，在保留完整观测时长（零观测裁剪）的前提下精准切分 `DeepSeek-V4-Flash` 跨流通信重叠边界；
  - `examples/structure/dsh_generalization_eval.py`：识别 `noflashcomm` 细胞拓扑（禁用 FlashComm 序列并行时 `sequence_parallel_factor = 1`），消除 `deepseek-v4.1` `tp4dp4_ep16_dspark7_noflashcomm` 12 个未解析案例（`12/12 = 100.0% <= 10%`，平均误差 `2.61%`），并强化 `45s/60s` 内外超时算术与有界内存工作池；
  - **575 个未注册留出集案例**：`575/575`（`100%`）成功解析比对，全种群口径 **573/575（99.65%）`<= 10%`**、**574/575（99.83%）`<= 15%`**（平均绝对相对误差 `3.49%`，中位数 `2.87%`），主种群口径 **575/575（100.00%）`<= 15%`**；
  - **全舰队合计 870 个实测案例**：**868/870（99.77%）`<= 10%`**、**869/870（99.89%）`<= 15%`**（平均绝对相对误差 `3.45%`，中位数 `2.87%`）。
