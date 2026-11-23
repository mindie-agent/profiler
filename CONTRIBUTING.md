# `mindie-profiler` 贡献指南

[English](CONTRIBUTING.en.md)

`mindie-profiler`（包名 `mindie_profiler`，`requires-python >= 3.11`）负责昇腾 NPU 受控性能采集、`msprof` SQLite/CSV/Trace 原地只读解析、`P0–P4` 显存归因、算子 C-ABI 与脱敏单算子复现生成（`inspect-op-abi` / `repro-op`）、集群 HCCL 互联标定（`fabric-probe`）、单卡/多卡真机基准套件（`bench {abi,sku,subgraph,pr-ab}`）、`mindie-model-structure/1` 三态拓扑对齐，以及向 `mindie-sim` 输出 C7 实测供给报告。

## 1. 扁平同级目录与链接 Worktree 开发流

保持主检出目录停留在干净 `main`，所有功能与修复统一在 `../.worktrees/` 下的独立链接工作树中完成：

```bash
git -C ../profiler fetch origin
git -C ../profiler worktree add -b feat/<topic> ../.worktrees/profiler-<topic> origin/main
cd ../.worktrees/profiler-<topic>
```

在沙箱化编码 Agent（Codex CLI、Claude Code 等）中工作时，请同时开放 `../profiler` 与 `../.worktrees/profiler-<topic>` 的目录访问权限，使 Git Worktree 元数据能正常写入 `../profiler/.git/worktrees/`。

## 2. 跨仓 SSOT 单源边界与上游真源纪律（必读）

1. **单一事实源（SSOT）统一委托至 `mindie-sim`**：
   - 模型目录几何（`sim_bridge_catalog.py`）、昇腾 A2 / A3 双 Die / A5（`Ascend950DT_*` / `Ascend950PR_9579` / `Ascend950PR_958b`）硬件规格与峰值（`hardware_presets.py`）、观测通信/融合/量化/张量契约（`body_*_contracts.py`、`tensor_contracts.py`）以及闭式子图代数算力/访存计算（`mindie_sim.subgraph_math`）**严禁在 `mindie-profiler` 本地重复维护副本**，必须统一委托给 `mindie-sim`。
   - 所有转发模块采用 **PEP 562 `__getattr__` 惰性转发**：`mindie_profiler` 顶层导入绝不能立即加载 `mindie_sim` 重型模块或触发任何设备上下文，确保 `python -I` 隔离导入耗时与 `0 MiB` HBM 增量契约成立。
2. **全栈上游源码真源路由与最新 `HEAD` 核对**：
   - 新增或更新算子归一化规则、C-ABI 目录（`op_api_catalog.json`）或 Advisor 诊断规则时，若算子不在 `vllm-ascend` 或 `cann/ops-transformer`，必须按职责边界挂载并核对对应的真实上游仓最新 `HEAD` 源码与实测抓包——包括推理与模型配方层的 **`vllm-ascend`、`cann-recipes-infer`、`MindIE-SD`、`xllm`**，CANN 算子层的 **`cann/ops-transformer`、`cann/ops-nn`、`cann/catlass`、`torch-npu`**，以及专项/内核层的 **`fla-npu`（KDA/GDN 线性注意力）、`flash-attn-npu`（Flash/稀疏注意力）、`AscendC` / `Triton-Ascend`、`xllm-ops`**。
   - 当历史 Issue 描述与最新真实源码/抓包冲突时一律以真实源码 + 抓包为准：例如 Advisor 必须在通用 `topk` / `scatter` 规则前优先识别已融合的 `MoeGatingTopK`、`MoeInitRoutingV3` 与缓存 epilog（避免误报重复融合建议）；CSV `--auto-step` 必须依赖真实 `Step Start Time(us)` 时间戳而非由 Step ID 伪造起点；C7 矩阵流水线发射率认证（`measured_supply_rules.py`）以内核与封装层源码哈希（`analyze_profile(..., implementation_evidence=...)` 或同目录 `status.json` `"implementation"`）为主判据，容器镜像摘要仅作辅助佐证。
3. **声明式基准配置表、1:1 算子构建器与魔法数字卫生**：
   - 基准测试 Shape 网格、容量边界、SKU L2 容量表与 HCCL 互联路由/排布预设统一存放在声明式数据文件 [`mindie_profiler/bench/bench_profiles.json`](mindie_profiler/bench/bench_profiles.json) 与 [`mindie_profiler/knowledge/fabric_probe_presets.json`](mindie_profiler/knowledge/fabric_probe_presets.json) 中，**严禁将基准网格或边界常数硬编码在 Python 代码里再批量写入 [`scripts/magic_number_exceptions.json`](scripts/magic_number_exceptions.json) 豁免**。
   - `mindie_profiler/bench/operators_{norm_quant,attention_mla,moe_comm,recurrent_mhc,common}.py` 维护 1:1 快速失败（fail-fast）算子构建器注册表：严禁使用 `inspect.signature`、严禁回退为组合 PyTorch 算子或 `"unmapped_catalog_op"` 占位；遇到未建模算子或缺失运行时内核必须立即抛出携带 `mindie-unmodeled-structure-hint/1` 载荷的 `BenchUnmodeledOperatorError`。所有基准与探测回执必须剔除宿主机用户主目录路径、IP 地址、设备节点路径、镜像仓库前缀与镜像摘要。

## 3. 本地环境隔离与测试验证

测试套件通过 `tests/conftest.py` 与 `tests/temp_workspaces.py` 自动隔离环境变量并在退出时清扫临时目录（零宿主机污染）：

```bash
# 1. 检查全仓 Unix LF 行尾与无新增未豁免魔法数字
python3 .github/scripts/check_lf_eol.py
python3 -B scripts/check_no_magic_numbers.py \
  --root profiler=mindie_profiler \
  --baseline scripts/magic_number_baseline.json \
  --exceptions scripts/magic_number_exceptions.json

# 2. 预编译 mindie-sim C 加速器并运行全量非真机测试（Tier 0 + Tier 1）
python3 -B -c "import mindie_sim.prediction.runtime.accel_build as b; b.build_accel()"
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. 连接常驻 A2 / A3 / A5 昇腾节点时运行 Tier 2 非破坏性真机集成测试
pytest -q -m live_npu
```

## 4. 独立 Wheel 安装冒烟测试

提交前请在仓库目录之外验证打包后的 Wheel，确保无遗漏包内数据文件（`bench/*.json`、`knowledge/*.json`、CANN 9.x C/H 头文件）或隐式相对路径假设：

```bash
uv build
tmpdir="$(mktemp -d)"
uv venv "$tmpdir/venv"
uv pip install --python "$tmpdir/venv/bin/python" --no-deps dist/*.whl
(cd "$tmpdir" && "$tmpdir/venv/bin/mindie-profiler" --help && "$tmpdir/venv/bin/mindie-profiler" bench --help && "$tmpdir/venv/bin/mindie-profiler" fabric-probe --help)
rm -rf "$tmpdir"
```

## 5. Pull Request 设计原则门禁（`device-tool` Profile）

每个 PR 须填写 [`.github/pull_request_template.md`](.github/pull_request_template.md) 并通过 `python3 .github/scripts/check_pr_checklist.py --profile device-tool`，为以下四项 `device-tool` 门禁提供实证记录（纯文档修改可标注 `not-applicable: docs-only`）：

- `DEV-ZERO-CTX`：离线解析、C-ABI 查询与 PEP 562 惰性 `mindie-sim` 桥接路径绝不导入 `torch_npu` 或在 `Phy-ID 0` 分配显存（`0 MiB` HBM 增量）。
- `DEV-READONLY-PATH`：原地只读打开用户 Profiling 产物（仅对已封存无侧车 DB 的 `CANTOPEN` 启用 `immutable=1`，严禁对 `SQLITE_BUSY` 启用），CAS/Shim/Sidecar 缓存严格遵守符号链接/NTFS 重解析点拒绝与原子 `os.replace`，采集停止与恢复先于回执落盘，并在 `except OSError:` 前透传 `TimeoutError`。
- `DEV-TOPOLOGY`：严禁在本地复制模型目录、硬件峰值、观测契约或子图数学公式（统一 SSOT 委托 `mindie-sim`）；保持 `mindie-model-structure/1` 三态结构归因、跨卡时钟对齐、A2/A3 双 Die/A5（`DT` + `PR_9579/958b`）精确解析及所属全栈上游仓（`vllm-ascend` / `cann-recipes-infer` / `MindIE-SD` / `ops-transformer` / `ops-nn` / `cann/catlass` / `fla-npu` / `flash-attn-npu` / `AscendC` / `Triton-Ascend` 等）最新源码算子分类一致，缺少完整 cohort 时诚实返回 `declared_only` / `unavailable`。
- `DEV-BOUNDED-MEM`：大体积 Trace 采用 `ijson` 流式扫描与按不相交窗口隔离的单窗口 PMU 预热（内存峰值 `<= 512 MiB`），核心模块保持 `< 800` 行及顶部 30 行内四段式契约头，通过 `check_no_magic_numbers.py`，全仓使用 Unix `LF`。
