# mindie-profiler 0.5.15

[English](profiler-0.5.15.en.md)

本版本是存储生命周期专项修复版，完整保留 `0.5.14` 的 `mindie-sim 0.9.14` 配套关系、CANN 9.x 稳态采集、算子 C-ABI 目录、单算子独立复现器、集群互联探测与 `ACLGraph` 诊断能力；所有变更只收敛长期运行与测试过程中的磁盘缓存、内容寻址库和临时目录泄漏，不改变既有测量口径与回执 schema：

- **CANN 9.x 采集 Shim 缓存有界化与编译超时清理（`mindie_profiler/cann_abi.py`）**：
  - `subprocess.TimeoutExpired` 继承自 `SubprocessError` 而非 `TimeoutError`，旧实现会绕过超时分支并遗留 `.<shim>.tmp.<pid>`；现在编译超时统一转换为内建 `TimeoutError`，未发布的临时对象在 `finally` 中确定性删除，只有成功 `os.replace` 的产物才会保留。
  - 发布成功后按修改时间仅保留最新 `8` 个 `libmindie_cann9_capture_*.so` 变体，并同步清理被淘汰变体的 `.*.lock`；超过 `3600s` 的中断编译 `*.tmp.*` 叶子被清扫；被进程映射或占用的 `.so` 删除失败仅忽略 `OSError`，不会把成功构建降级为失败。
- **`/tmp/mprof` 内容寻址复现库与 diff 目录有界保留（`mindie_profiler/repro_retention.py`）**：
  - 新增 `prune_repro_storage(root, *, max_entries=64, max_age_days=14)`，分别约束 CAS 槽（`<sha>/repro.py` + `manifest.json`）与 diff 槽（`diff/<id>/diff.json`）的数量与年龄，避免短根（`MINDIE_REPRO_SHORT_ROOT`）无限增长。
  - 严格跳过进程提交登记表 `_PROTECTED_INODES`（即 `_protected_inodes()` 的已提交分量）、已注册/活跃槽、锁标记条目、符号链接以及包含未知载荷的目录；淘汰只删除已知常规叶子后再移除空目录，逐项失败均为 best effort。
  - 每次 `stage_artifacts` 成功投递后机会式执行一次；淘汰失败不会把已投递工件降级为 `delivery_failed`。
- **Trace sidecar 索引原子重建与 WAL 上限（`mindie_profiler/sources_trace.py`）**：
  - 重建先写入私有 `.<index>.tmp.<pid>` 数据库，成功关闭后连同已检查点的 `-wal`/`-shm` 一起发布；失败或解析中断（含 `ProfilerSchemaError`）会删除临时库及其 sidecar，不再留下半成品索引。
  - 索引连接设置 `PRAGMA journal_size_limit = 8388608`，关闭前执行 `PRAGMA wal_checkpoint(PASSIVE)`，`.mindie-trace-index.sqlite3-wal` 不再随 Trace 无界膨胀；超过 `6` 小时的僵尸构建库会在下一次建索引时清扫。
- **测试套件临时目录零残留（`tests/temp_workspaces.py`、`tests/conftest.py`）**：
  - 新增进程级临时工作区登记表：`nr4-probe-*` 双线程探测工作区、`mpr_` 短根以及 `mp_`、`mpc_`、`r6cas-`、`r6sup-`、`r7cas-`、`r10...-`、`nr_s6_r11root_` 等 `/tmp` 根统一登记。
  - 每个测试的 autouse fixture `finally` 与进程 `atexit` 双重兜底回收，断言失败、超时或线程启动异常都不再遗留目录；`run_ranks` 异常退出时立即释放自身工作区。
- **回归测试（`tests/test_storage_lifecycle_contracts.py`）**：
  - Tier 0/1 覆盖编译超时临时对象清理、shim 缓存上限与陈旧临时文件清扫、CAS/diff 年龄与数量淘汰及活动状态保护、机会式淘汰、sidecar 构建失败清理与 WAL 上限、`run_ranks` 在 `TMPDIR`/`/tmp` 的零新增目录。
