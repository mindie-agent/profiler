# 模型结构、实测归因与性能预测统一验证管线

`examples/structure/pipeline.py` 是本仓库唯一的公开离线回放与验证入口，`cases.json` 是唯一的测试场景清册，`results/` 保存当前受控输出摘要。每轮验证均从同一个固定版本的 `mindie-sim` 包重新运行预测，同时记录包内容 SHA256 与源码提交哈希，严禁跨版本按误差高低挑选历史结果。原始大体积采集文件、逐源完整分层报告与校准训练证据保存在 Git 仓库外部，通过 SHA256 内容指针精确关联。

- 历史多代际留出集回放中的原生算子校准、物理适用域与首次执行等待边界详见 [`NATIVE_OBSERVATIONS.md`](NATIVE_OBSERVATIONS.md)（单算子校准与整网 Body 精度分开独立验收）。
- 显式按需启用（opt-in）的冻结 A2/A5 限定域原生校准及其完整真实分母详见 [`QUALIFIED_NATIVE_CALIBRATION.md`](QUALIFIED_NATIVE_CALIBRATION.md)（默认回放路径不受影响）。

## 运行方式

安装好本项目测试依赖及配套 `mindie-sim` 后，在仓库根目录执行：

```bash
python examples/structure/pipeline.py --phase decode \
  --output examples/structure/results/decode.json \
  --archive-root /path/to/external-evidence --workers 2

python examples/structure/pipeline.py --phase prefill \
  --output examples/structure/results/prefill.json \
  --archive-root /path/to/external-evidence

python examples/structure/pipeline.py --scope operators --phase decode \
  --output examples/structure/results/operators.json \
  --archive-root /path/to/external-evidence

python examples/structure/pipeline.py --scope engine \
  --output examples/structure/results/engine.json \
  --archive-root /path/to/external-evidence

python examples/structure/pipeline.py --scope generalization \
  --output examples/structure/results/generalization.json \
  --archive-root /path/to/external-evidence
```

- **单场景与增量刷新**：通过 `--case-id ID` 可指定单个场景，`--prediction-timeout` 设置单次预测超时上限。配合 `--update` 进行增量刷新时，仅当其他条目的 `mindie-sim` 内容哈希、完整 Case 定义与外部证据 SHA256 完全未变时才保留原记录；一旦模型定义或仿真运行时发生变化，必须全量重跑，绝不按历史误差择优拼表。不带 `--case-id` 执行 `--update` 时，会自动重放新增或定义变更的场景，对未变更场景仅校验证据完整性并刷新清册关联。
- **并发预算与原子发布**：多进程并发度（`--workers`）受本机实际可用 CPU 与内存约束，单个预测子进程工作集上限为 `512 MiB`。运行期间清册、模型配置与 `mindie-sim` 包保持只读不可变；所有选定场景全部执行完毕后才原子替换 `results/` 下的主记分牌（中途中断不会覆盖已有完整记分牌，已完成场景的外部 SHA256 归档仍会保留；单场景 `--case-id` 调试不会覆盖全量记分牌）。任何场景失败均保留原始错误原因并以非零状态码退出。

## 本地长上下文采集增量接入

无需启动 NPU 设备或远端任务，可直接通过同一管线入口发现并提取本地已有的长上下文采集目录：

```bash
python examples/structure/pipeline.py \
  --discover-local /path/to/local-captures \
  --capture-pattern '*_128k_decode_*' \
  --template-case-id decode:existing-source-id \
  --output /path/to/external-evidence/local-capture-intake.json \
  --archive-root /path/to/external-evidence --update
```

- **提取与预测两步分离**：`--discover-local` 仅流式提取设备侧实测证据；加上 `--update` 会将完整 Decode 来源追加登记至 `cases.json`（不在此步执行仿真预测），省略 `--update` 则仅输出候选目录与提取预览。登记完成后，再运行常规 `--phase decode --update` 对新增来源执行预测对账。
- **模板绑定与目录粒度**：若新部署尚无已登记的同类场景，可通过 `--template-case-path cases/source-model.json` 传入经核验的模型声明文件（与 `--template-case-id` 二选一，不会向清册写入占位条目）。若扫描根目录本身就是单次采集下的 `prof/` 目录，请传入具体叶子目录通配符（如 `--capture-pattern 'decode_*'`），避免将包含多次实验的父目录误识别为单次采集。缺少设备 CSV、仅含 Prefill、模板匹配不唯一或上下文证据缺失均分类如实报告，绝不拿 API 汇总表或目录名充当 Decode Body。重复内容自动跳过；多 Rank 目录优先选取唯一的 `tp0` / `rank0`，存在歧义时保留缺口标记。
- **部署与请求元数据解析**：支持读取 `capture_metadata.json`、`benchmark_summary.json`、`profile_evidence.json` 与 `manifest.json`。`capture_parameters` 或 `source_configuration` 中的 `model/hardware/tp/dp/ep/quant` 以及生产摘要中的 `model_path`、`tensor_parallel_size`、`extra.recipe`、`extra.quantization` 和显式硬件 SKU 均作为显式部署条件校验。同标签的 `client_cell.json`（或按 `summary.cell` 命名的 Profile JSON）用于提取真实请求 Token 用量，实际 `prompt_tokens` 优先于标称前缀长度（例如 `4096` 前缀加 `8` 后缀的真实输入长度为 `4104`）；缺失 `usage` 时仅保留显式请求长度条件，`DP`/`EP` 缺失绝不默认补 `1`。若实测元数据中的 `TP/DP/EP` 或硬件 SKU 与所选模板冲突，直接拒绝接入；未显式传入 `--template-case-id` 时，清册顶层 `capture_templates` 必须存在唯一精确匹配：
  ```json
  {"capture_templates": [{"case_id": "decode:existing-source-id", "match": {
    "model": "declared-model", "hardware": "declared-sku", "tp": 16, "dp": 1,
    "ep": 16, "quant": "declared-quantization"
  }}]}
  ```
  模板仅用于提供采集文件未记录的静态部署声明，选择过程不读取历史误差或通过率；无逐步序列长度记录时，绝不把目录名中的 `128k`、KV 缓存池上限或页表容量当作实际有效上下文长度。
- **多几何样本桶（Population Bucket）全量计分**：新接入来源默认启用 `geometry_limit: null`，对采集内出现的所有 `(Batch, Query)` 几何样本桶逐桶评估（存量旧清册条目默认仍评估样本数最多的主几何桶）。输出中的 `geometry_comparisons` 按桶分别记录调用次数、Mean/P50/P90、预测值与误差，绝不将不同 Batch 规模的单层耗时混算。`population_coverage` 显式列出已覆盖调用占比，`source_all_populations_passed` 仅在所有几何桶均完成计分且全部达标时为 `true`。源级主指标（Headline）固定取完整 Forward 次数最多的主样本群（并列时保持输入顺序，不按误差择优）；其余爬坡或收尾阶段的候选样本群逐桶并列展示，既不掩盖其他样本桶的未达标项，也不单凭样本数最多推定 Host 已进入稳态。
- **算子全集证据（`operator_population_evidence`）复用**：已提取的完整原生算子样本全集可通过清册中的 `operator_population_evidence` 登记复用（锁定 `actual` 与 `mapping` 文件的路径、文件大小及 SHA256）。回放时管线逐项核验源码契约、候选层集合、算子角色与融合边界，并调用当前版本的 `mindie-sim` 重新计算物理成本，既不重扫原始大体积 CSV，也不复用旧预测值。契约或融合边界发生变化的算子群会被明确排除；未映射算子族的少量抽样不能替代算子全集。若 Body 提取文件仅更新了外围记账字段，可在逐项核验完整 Forward 数、层边界与张量几何完全一致后通过 `retained_body_identity` 复用。

## 数据与计量边界

- **职责与身份分离**：`cases/*.json` 保存模型结构、并行部署、源码程序与物理服务参数；`cases.json` 清册记录采集源、模型定义、提取产物与校准证据的 SHA256 身份。核心事件解析与张量契约唯一归属 `mindie_profiler/`，声明式结构与物理资源成本唯一归属 `mindie-sim`。
- **Decode 分层并集核算**：依据完整层拓扑、张量几何与输出 Head 边界自动切分 Decode Body，分别报告完整层的设备活动并集、层内未覆盖间隙、首层（Layer 0）与稳态层耗时，而非简单累加所有 Kernel 耗时。
- **跨 Head 通信摘要的条件上界**：对于缺少设备 Task/Stream 绑定且时间跨度越过同次 Forward 输出 Head 的通信汇总行，仅在隐藏态生产者与后继消费者链路完整时，才以消费者起始时间给出条件结束上界（原始摘要区间与定位信息完整保留，真实设备 Task 绝不裁剪，且该条件上界不作为实测通信服务时间参与严格算子计分）。
- **Prefill 分块与算子容差**：Prefill 对完整实测 Chunk 逐一预测并累加 Body 耗时；当 Query 总量与声明不一致时，绝不拿局部切片冒充完整请求。严格同构算子群（Cohort）要求具备相同的张量契约与物理工作量（源码条件参考项单独列出）：单次调用 `> 50 us` 采用 `15%` 相对容差，`<= 50 us` 采用 `15 us` 绝对容差。
- **Engine 端到端与物理域冻结**：Engine 评估消费完整客户端请求记录与真实 `completion_tokens` 计数，设备调度周期、客户端 Token TPOT、流式 Chunk 间隔、TTFT 与总吞吐各自保留独立分母，未观测到的外围耗时不臆断为 Host 空泡。图模式下的自动拓扑定位属于结构条件推断，精确单次调用绑定仍需 Host/Module 级证据支撑。物理服务域按算子实现、数值精度、内存布局与执行边界划分，训练集与留出集源 SHA256 在读取留出集耗时前严格冻结。

## 模块职责一览

| 模块 | 核心职责 |
| --- | --- |
| `pipeline.py` | 清册筛选、源内容哈希核验、单版本运行时锁定、受限并发调度、外置证据归档与记分牌原子更新 |
| `body.py` / `decode.py` | `mindie-sim` Body 语义时间线对接、Decode 前向窗口提取与逐层对账 |
| `prefill.py` | 完整 Prefill Chunk 识别、DP-partner 对齐与 Body / TTFT 边界切分 |
| `engine.py` | 客户端请求记录、设备调度周期、外围/MTP 区间核算与正式 Serving 预测评估 |
| `operators.py` / `cohorts.py` | Body 内原生算子族提取、同构算子群聚合与物理成本对账 |
| `references.py` | 源码条件参考对照（与严格同构 Cohort 计分显式隔离） |
| `service_evidence.py` | 服务参数执行证据管理与冻结物理域泛化校验 |

## 阶段性回放结果与报告生成

> [!NOTE]
> 以下 `results/` 报告为基于特定采集子集与对应校准边界生成的离线回放摘要，阅读与引用时须同时遵循仓库主文档 [`README.md` 基准数据集清单与独立精度证据边界](../../README.md#基准数据集清单与独立精度证据边界) 中的分母与独立性说明。

- [Decode 结构回放摘要（280 个登记场景 `<= 15%`）](results/decode.md)
- [Prefill Body 与 TTFT 回放摘要（15 个登记场景 `<= 15%`）](results/prefill.md)
- [Engine 与客户端边界对账报告](results/engine.md)
- [物理服务域留出验证报告](results/generalization.md)
- [未登记全舰队留出采集泛化评估报告](results/dsh_full_generalization.md)
- [整网 4D 效率与 `30 ms` SLA 硬件缩放报告（历史快照）](results/efficiency_and_scaling.md)

重新生成或刷新整网 4D 效率报告与留出集泛化评估报告：

```bash
python examples/structure/efficiency_report.py \
  --json-out examples/structure/results/efficiency_and_scaling.json \
  > examples/structure/results/efficiency_and_scaling.md

python examples/structure/dsh_generalization_eval.py
```

所有入库结果 JSON 体积均控制在 `5 MB` 以内，逐源完整分层与预测明细可通过报告中的 SHA256 证据指针在外部归档目录中检索。
