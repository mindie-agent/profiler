# mindie-profiler 0.5.1：流式原生库 SHA256 校验、SQLite 锁超时收敛与 CLI 根命令契约补齐

[English](https://github.com/mindie-agent/profiler/blob/v0.5.1/docs/releases/profiler-0.5.1.en.md)

`mindie-profiler 0.5.1` 完成流式原生库 SHA256 校验（消除全文件 `read_bytes()` 内存峰值）、SQLite 读写锁 `busy_timeout >= 3000ms` 统一收敛、`TimeoutError` 显式透传（禁止被 `except OSError:` 静默吞没）以及 CLI 根命令 `-h/--help` 与未知子命令退出码契约补齐。

---

## 一、核心特性与行为变更

### 1. 流式原生库 SHA256 摘要校验（`mindie_profiler/vllm_online_evidence.py`，PR `#5`）

- 在线证据采集在计算大型原生动态库（`.so`）SHA256 摘要时，改用二进制流式 `hashlib.file_digest(fh, "sha256")`，不再通过 `Path.read_bytes()` 将整个共享库文件一次性读入进程内存，严格遵循有界工作集（`<= 512 MiB` 控制面内存上限）约束。

### 2. SQLite `busy_timeout >= 3s`、`TimeoutError` 透传与测试宿主机隔离（PR `#6`）

- **SQLite 并发锁等待收敛**：在 `memory_db.py`、`sources_db.py`、`sql.py` 等 SQLite 连接入口统一配置 `timeout=5.0` 与 `PRAGMA busy_timeout=5000`（读写连接启用 `PRAGMA journal_mode=WAL`），避免多进程并发读取/写入 Profiling 证据库时因瞬时锁竞争立即抛错。
- **`TimeoutError` 显式透传**：由于 Python 3.11+ 中 `TimeoutError` 是 `OSError` 的子类，全面梳理 `analyze.py`、`collect.py`、`compare_acceptance.py`、`framework_capture.py`、`inventory.py`、`memory_evidence.py`、`memory_sampler.py`、`segment.py`、`sources_csv.py`、`sources_trace.py`、`tensor_cast_provider.py`、`theoretical_model.py`、`thermal_guard.py`、`vllm_online_evidence.py`、`vllm_online_memory.py` 与 `weight_inspector.py` 中的 `except OSError:` 分支，显式前置 `except TimeoutError: raise`，严禁将超时信号静默降级为空结果或普通文件缺失。
- **测试子进程超时与环境隔离**：为 `tests/test_profiler_provider.py` 中的 `git` 子进程调用补齐显式 `timeout=5`，并在 `tests/conftest.py` 中隔离宿主机环境变量，确保 Tier 0/Tier 1 测试可重入、无残留副作用。

### 3. CLI 根命令帮助输出与未知子命令诊断契约（`mindie_profiler/__main__.py`，PR `#6`）

- 新增 `_root_parser()` 处理顶层 `mindie-profiler -h` / `--help`，清晰展示支持的全部子命令（`inventory`、`analyze`、`correlate`、`compare`、`sql`、`collect`）及默认 `analyze` 行为说明。
- 当传入未知非选项子命令（如 `mindie-profiler unknown-cmd`）时，不再将其误转发给默认 `analyze` 解析器产生令人困惑的参数报错，而是直接向 `stderr` 输出 `mindie_profiler: unknown command ... (choose from ...)` 并以退出码 `2` 终止。

---

## 二、验证结果与证据边界

- **自动化测试结果**：全量非在网单测（`pytest -q -m "not live_npu"`，包含新增的 `tests/test_profiler_cli_root.py`）全部通过。
- **证据边界说明**：本版本聚焦于 `mindie-profiler` 本地分析引擎、在线证据采集流式内存边界、SQLite 锁超时与 CLI 入口契约收敛，不改变 C7 `mindie-profile-summary/1` 报告 Schema 结构。
