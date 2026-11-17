# `mindie-profiler` 贡献指南

[English](CONTRIBUTING.en.md)

`mindie-profiler`（包名 `mindie_profiler`，`requires-python >= 3.11`）负责昇腾 NPU 受控性能采集、`msprof` SQLite/CSV/Trace 原地只读解析、`P0–P4` 显存归因、算子 C-ABI 与脱敏单算子复现生成（`inspect-op-abi` / `repro-op`）、`mindie-model-structure/1` 三态拓扑对齐，以及向 `mindie-sim` 输出 C7 实测供给报告。

## 1. 扁平同级目录与链接 Worktree 开发流

保持主检出目录停留在干净 `main`，所有功能与修复统一在 `../.worktrees/` 下的独立链接工作树中完成：

```bash
git -C ../profiler fetch origin
git -C ../profiler worktree add -b feat/<topic> ../.worktrees/profiler-<topic> origin/main
cd ../.worktrees/profiler-<topic>
```

在沙箱化编码 Agent（Codex CLI、Claude Code 等）中工作时，请同时开放 `../profiler` 与 `../.worktrees/profiler-<topic>` 的目录访问权限，使 Git Worktree 元数据能正常写入 `../profiler/.git/worktrees/`。

## 2. 本地环境隔离与测试验证

测试套件通过 `tests/conftest.py` 与 `tests/temp_workspaces.py` 自动隔离环境变量并在退出时清扫临时目录（零宿主机污染）：

```bash
# 1. 检查全仓 Unix LF 行尾
python3 .github/scripts/check_lf_eol.py

# 2. 预编译 mindie-sim C 加速器并运行全量非真机测试（Tier 0 + Tier 1）
python3 -B -c "import mindie_sim.prediction.runtime.accel_build as b; b.build_accel()"
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. 连接常驻 A2 / A3 昇腾节点时运行 Tier 2 非破坏性真机集成测试
pytest -q -m live_npu
```

## 3. 独立 Wheel 安装冒烟测试

提交前请在仓库目录之外验证打包后的 Wheel，确保无遗漏包内数据文件（`knowledge/*.json`、CANN 9.x C/H 头文件）或隐式相对路径假设：

```bash
uv build
tmpdir="$(mktemp -d)"
uv venv "$tmpdir/venv"
uv pip install --python "$tmpdir/venv/bin/python" --no-deps dist/*.whl
(cd "$tmpdir" && "$tmpdir/venv/bin/mindie-profiler" --help)
rm -rf "$tmpdir"
```

## 4. Pull Request 设计原则门禁（`device-tool` Profile）

每个 PR 须填写 [`.github/pull_request_template.md`](.github/pull_request_template.md) 并通过 `python3 .github/scripts/check_pr_checklist.py --profile device-tool`，为以下四项 `device-tool` 门禁提供实证记录（纯文档修改可标注 `not-applicable: docs-only`）：

- `DEV-ZERO-CTX`：离线解析、C-ABI 查询与 `sim` 桥接路径绝不导入 `torch_npu` 或在 `Phy-ID 0` 分配显存（`0 MiB` HBM 增量）。
- `DEV-READONLY-PATH`：原地只读打开用户 Profiling 产物，CAS/Shim/Sidecar 缓存严格遵守符号链接/NTFS 重解析点拒绝与原子 `os.replace`，并在 `except OSError:` 前透传 `TimeoutError`。
- `DEV-TOPOLOGY`：保持 `mindie-model-structure/1` 三态结构归因、跨卡时钟对齐与 A2/A3 双 Die/A5 拓扑语义精确，绝不伪造单卡兜底。
- `DEV-BOUNDED-MEM`：大体积 Trace 采用 `ijson` 流式扫描与 SQLite 按需切片（内存峰值 `<= 512 MiB`），核心模块保持 `< 800` 行及顶部 30 行内四段式契约头，全仓使用 Unix `LF`。
