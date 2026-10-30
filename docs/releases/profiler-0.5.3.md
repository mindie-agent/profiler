# mindie-profiler 0.5.3

本版本配套 `mindie-sim 0.8.1`，完成 A3/A5 全量注册 Decode（280 case）与 Prefill（15 case）长短上下文收敛、全舰队 DSH 留出集（561 case）零样本泛化评估管线，以及整网算子级 4D MFU/MBU/CV 效率剖析与 30ms SLA 硬件扩缩容吞吐评估工具。

- **注册 Decode 与 Prefill 全量收敛**：
  - `examples/structure/results/decode.md`：280/280（100.0%）通过 15% 门禁，253/280（90.4%）误差 <= 10%，平均绝对相对误差 4.40%（中位数 3.36%），新增 187 个 64K/96K/128K 长序列案例 100% 落在 10% 以内；
  - `examples/structure/results/prefill.md`：15/15（100.0%）可比 Prefill Body 案例误差 <= 8.42%（平均绝对相对误差 4.01%）。
- **DSH 全舰队 743 捕获解析与 561 留出集零样本泛化（`examples/structure/dsh_generalization_eval.py`）**：
  - 支持 `mhc_final_norm` 终态 RmsNorm 在 AllGather 前完成的流折叠识别（`mindie_profiler/decode_segmentation.py`）；
  - 全舰队合计 856 个可比案例中 **841/856（98.25%）<= 15%**、**736/856（85.98%）<= 10%**（平均绝对相对误差 5.44%，中位数 4.60%）；561 个未注册留出集 **546/561（97.33%）<= 15%**（平均绝对相对误差 5.99%，中位数 5.10%）。
  - 执行管线强制有界内存（`< 50 MiB` 驻留工作集）、CPU/内存双门限并发池、60s 单步硬超时与含 `client_cell.json` 及模拟器身份的缓存键校验。
- **整网 4D 效率、0.80x MBU 拟合与 30ms SLA 扩缩容报告（`examples/structure/efficiency_report.py`）**：
  - 输出算子级与整网 `Cube_MFU`、`Vec_MFU`、`MBU`、`Link_Util`、`CV_Overlap` 拆解、0.80x MBU 目标屋脊线拟合，以及 `1x` vs `2x HBM` vs `2x Compute` 在 Decode SLA `<= 30ms` 下的可行并发与吞吐收益对比。
