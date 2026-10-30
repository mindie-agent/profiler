# 结构、实测与预测的统一验证管线

`pipeline.py` 是唯一公开回放入口，`cases.json` 是唯一 Case 清册，`results/` 保存当前结果。
每一轮从同一个固定的 Sim 包重新预测，记录包内容 SHA256 和已安装源码提交，不按误差选择旧结果。
原始采集、逐源完整报告及训练证据保留在仓库外，以 SHA256 指针关联。

## 运行

在安装本项目测试依赖和配套 Sim 后，从仓库根目录执行：

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

`--case-id ID` 可以选择单一场景；`--prediction-timeout` 设置单次预测预算。
选定场景时可加 `--update` 增量刷新当前结果：仅保留同一 Sim 内容哈希、完整 Case 定义和证据 SHA256 均未变化的其他行。变更模型或运行时必须重放，不按历史误差挑选结果。
不指定 `--case-id` 的 `--update` 自动重放新增或定义发生变化的场景；没有变化时仅核验已有证据并刷新清册关联。
多 worker 按实际可用 CPU/RAM 限制，每个预测工作集预算 512 MiB。
清册中的本地采集路径需可读；迁移数据时更新路径并保留、核验内容 SHA256。
清册、模型和 Sim 包在一次运行内不可变。结果逐源写入，失败保留原始原因并使入口返回非零。

## 本地长上下文采集增量接入

已有采集可通过同一个入口发现和提取，不启动设备或远程任务：

```bash
python examples/structure/pipeline.py \
  --discover-local /path/to/local-captures \
  --capture-pattern '*_128k_decode_*' \
  --template-case-id decode:existing-source-id \
  --output /path/to/external-evidence/local-capture-intake.json \
  --archive-root /path/to/external-evidence --update
```

此模式只流式提取设备证据；`--update` 将完整 Decode 来源追加到唯一 `cases.json`，不执行 Sim 预测。
省略 `--update` 时只返回候选与提取结果。随后使用正常 `--phase decode --update` 回放新增来源。
新部署尚无已登记来源时，可用 `--template-case-path cases/source-model.json` 提供已核验的模型声明；它与 `--template-case-id` 二选一，不会向清册写入占位来源。
当根目录是某次采集的 `prof/` 时，使用实际叶子目录模式（例如 `--capture-pattern 'decode_*'`），避免把包含多个来源的父目录当作一次采集。
没有设备 CSV、只有 Prefill、模板不明确和上下文证据缺失分别报告；不会把 API 统计或目录名称变成 Body。
已登记的相同源内容不再提取，多 rank 目录优先唯一 `tp0` / `rank0`，有歧义时保留缺口。

元数据读取 `capture_metadata.json`、`benchmark_summary.json`、`profile_evidence.json`、`manifest.json`。
`capture_parameters` 或 `source_configuration` 中的 `model/hardware/tp/dp/ep/quant` 是显式部署声明。
同时支持生产摘要的 `model_path`、`tensor_parallel_size`、`extra.recipe`、`extra.quantization` 和明确硬件 SKU 字段。
同 label 的 `client_cell.json` 可提供完整请求 usage；实际 `prompt_tokens` 优先于 prefix 长度。
也支持生产器以自身 `summary.cell` 命名的 Profile JSON，以及 `requests[].usage` 中的实际输入/输出长度；同一目录存在多个匹配摘要时保留歧义。
例如 4096 prefix 加 8 suffix 的真实 usage 是 4104；usage 缺失时只保留显式请求长度条件，DP/EP 缺失不会补成 1。
明确的 TP/DP/EP 或 SKU 与模板冲突时拒绝接入，缺字段则仍需明确模板声明。
未指定 `--template-case-id` 时，清册顶层 `capture_templates` 必须有唯一的完整匹配：

```json
{"capture_templates": [{"case_id": "decode:existing-source-id", "match": {
  "model": "declared-model", "hardware": "declared-sku", "tp": 16, "dp": 1,
  "ep": 16, "quant": "declared-quantization"
}}]}
```

显式模板选择保留未观测的部署字段，不声称捕获已经证明这些条件。选择过程不读取历史通过率。
请求 prompt/output 形成条件范围与初始代表值；没有逐步序列长度时不把 128K 目录名、KV 缓存或页表容量当实际上下文。

新增来源的 `geometry_limit: null` 比较所有实际 B/q 桶。旧清册行默认仍只预测最大人口桶。
结果中的 `geometry_comparisons` 分别保存每桶调用数、Mean/P50/P90、预测与误差；不混算不同 B 的单层分布。
`population_coverage` 明示覆盖调用数，`source_all_populations_passed` 仅在全部桶均已评分且全部通过时为真。
源级 Headline 以完整 Forward 数最多的主群为准；同数时保持输入顺序，不按误差或预测成功与否择优。
其余爬坡/收尾候选群逐桶展示，不否决主群，但最大人口本身不代表 Host 已证实稳态。
全桶通过与覆盖率是独立审计，主群通过不会把其他群的失败改成通过。

回放期间保留上一份完整记分牌，全部选定来源执行完毕后才替换当前 JSON/Markdown；中途进度写入标准输出。
中断不会发布局部主表，已完成源的完整证据仍保存在外置 SHA256 归档中。
局部 `--case-id` 调试不能覆盖较大的已有记分牌；同运行时增量更新使用 `--update`，新运行时需完整重放。

已提取的完整原生算子人口可通过清册的 `operator_population_evidence` 复用，条目固定 actual 与 mapping 的路径、SHA256 和大小。
管线逐个验证源码合同、候选层集合、角色及融合边界，再用当前 Sim 重新计算物理成本，不重扫原始 CSV，也不复用旧预测。
合同或边界发生变化的 cohort 明确排除；未映射族的少量示例不能代替完整人口。
若 Body 提取文件只改变了外围记账，可附旧 `retained_body_identity`；必须验证完整 Forward、层边界和几何逐项相等后才能复用。
算子人口证据的登记不会使已核验的 Body 成本失效，算子比较本身仍需重新执行。

## 数据边界

- `cases/*.json` 保存模型、部署、源码程序与物理服务参数；清册保存采集、模型、提取结果和校准证据的内容身份。
- Decode 从完整拓扑、张量几何及 head 边界自动识别 Body。完整层的活动并集、内部间隙、层 0 与稳态层分别报告；不是把所有 kernel 耗时相加。
- 无设备 Task/Stream 绑定的通信摘要若跨越同次 Forward 的 Head，只在实际 hidden 生产者与后继 consumer 链完整时，以 consumer 开始时间给出条件结束上界。原摘要区间和定位信息仍保留，真实设备任务不裁剪；该上界不作为实测通信服务时间参与严格算子计分。
- Prefill 对实际完整 chunk 逐一预测，累加其 Body。query 总量与声明不一致时不把局部片段冒充完整请求。
- 算子严格 cohort 需要相同张量契约和物理工作量；源码条件参考单列。单次 >50 us 使用 15% 相对容差，<=50 us 使用 15 us 绝对容差。
- Engine 使用完整请求记录与实际 completion-token 数。设备 target cycle、客户端 token TPOT、文本 chunk 间隔、TTFT 和吞吐各自保留分母。缺失的外围区间不直接命名为 Host gap。
- 图模式的自动拓扑定位是结构条件推断；精确 occurrence 绑定仍需要 Host/module 证据。同构集合可以评分而无需猜测具体层。
- 服务域按真实实现、精度、布局和执行边界划分，以 local M/N/K、工作量或 payload 表示连续变化。跨 TP 迁移不复制单点耗时；通信 topology/ranks 保持独立。训练源与留出源 SHA 集合在读取留出耗时前冻结。

## 模块职责

| 模块 | 职责 |
|---|---|
| `pipeline.py` | 清册选择、源身份、同一运行时、有限并发、外置证据和当前记分牌 |
| `body.py` / `decode.py` | Sim Body 语义时间线、Decode 提取与分层对账 |
| `prefill.py` | 完整 Prefill chunk 识别与 Body/TTFT 分界 |
| `engine.py` | 请求、设备 cycle、Outer/MTP 区间和正式 Serving 预测 |
| `operators.py` / `cohorts.py` | Body 内原生算子族、同构集合及物理程序比较 |
| `references.py` | 不冒充严格 cohort 的源码条件参考 |
| `service_evidence.py` | 服务参数执行证据与冻结物理域泛化 |

核心事件解析和合同仍唯一归属 `mindie_profiler/`，声明结构和资源成本唯一归属 Sim。
旧日期/commit 过程目录、一次性构造脚本和跨历史预测拼接已从当前树删除。

## 当前结果

- [Decode](results/decode.md)
- [Prefill Body 与 TTFT](results/prefill.md)
- [Engine 与客户端边界](results/engine.md)
- [物理服务域留出验证](results/generalization.md)

JSON 小于 5 MB，逐源完整分层与预测详情可由其 SHA256 证据指针取回。
同源校准的通过率不等于盲测泛化；执行成功也不等于精度通过。
