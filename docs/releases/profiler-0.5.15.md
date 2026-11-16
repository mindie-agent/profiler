# mindie-profiler 0.5.15

[English](profiler-0.5.15.en.md)

本版本是存储生命周期专项修复版，完整保留 `0.5.14` 的 `mindie-sim 0.9.14` 配套关系、CANN 9.x 稳态采集、算子 C-ABI 目录、单算子独立复现器、集群互联探测与 `ACLGraph` 诊断能力；所有变更只收敛长期运行与测试过程中的磁盘缓存、内容寻址库和临时目录泄漏，不改变既有测量口径与回执 schema：

- **CANN 9.x 采集 Shim 缓存有界化与编译超时清理（`mindie_profiler/cann_abi.py`）**：
  - `subprocess.TimeoutExpired` 继承自 `SubprocessError` 而非 `TimeoutError`，旧实现会绕过超时分支并遗留 `.<shim>.tmp.<pid>`；现在编译超时统一转换为内建 `TimeoutError`，未发布的临时对象在 `finally` 中确定性删除，只有成功 `os.replace` 的产物才会保留。
  - 编译、发布与淘汰统一由 `cache_dir/.cann_abi_build.lock`（POSIX `flock` / Windows `msvcrt.locking`）加进程内线程锁串行化；不再创建或删除任何按变体的 `.*.lock`，避免淘汰时把并发 `flock` 等待者分裂到不同 inode 后同时编译同一 `.so`。
  - 每次编译使用 `.<shim>.tmp.<pid>.<随机 token>` 唯一临时名，同一进程的两个线程也不会碰撞；仅当非阻塞探测确认当前无活跃构建时，才清扫超过 `3600s` 的 `*.tmp.*` 残留。发布成功后按修改时间仅保留最新 `8` 个 `libmindie_cann9_capture_*.so` 变体，被进程映射或占用的 `.so` 删除失败仅忽略 `OSError`。
- **`/tmp/mprof` 内容寻址复现库与 diff 目录有界保留（`mindie_profiler/repro_retention.py`）**：
  - `prune_repro_storage(root, *, max_entries=64, max_age_days=14)` 分别约束 CAS 槽（`<sha>/repro.py` + `manifest.json`）与 diff 槽（`diff/<id>/diff.json`）的数量与年龄；当 `<root>` 或 `<root>/diff` 是符号链接或 Windows reparse point（含 NTFS junction，检查 `st_reparse_tag` / `FILE_ATTRIBUTE_REPARSE_POINT`）时整体拒绝淘汰，候选条目与叶子同样跳过。
  - 删除前统一预验证所有叶子：目录内容必须属于已知叶子集合，且每个存在的叶子都是非 reparse 常规文件；`repro.py` 为常规文件而 `manifest.json` 为符号链接的部分损坏槽不会留下半删除状态。
  - 写入方在 `<root>/.retention.lock` 跨进程锁下发布 `.<slot>.write-*` 标记后才写叶子，并在 inode 进入保护集合后移除；淘汰方同时持有 `repro_storage._LOCK` 与同一 OS 锁，在同一临界区内重新核对 `_SLOTS`、`_REGISTRY`、`_PROTECTED_INODES`、锁/写入标记与叶子 inode，把条目原子 `os.replace` 到 `.trash-*` 后才释放锁，消除 check-then-delete TOCTOU；随后只删除重新验证过的常规叶子，并清扫残留 `.trash-*` 与超过 `3600s` 的孤儿写入标记。
  - 每次 `stage_artifacts` 成功投递后机会式执行一次；淘汰失败不会把已投递工件降级为 `delivery_failed`。
- **Trace sidecar 索引原子重建与单文件发布（`mindie_profiler/sources_trace.py`）**：
  - 每次重建使用 `.<index>.tmp.<pid>.<随机 token>` 唯一私有库，并在创建前取得其 `.lock` 所有权锁；`_open_index()` 与整个构建/发布都包在 `try/finally` 内，PRAGMA 失败、`ProfilerSchemaError` 或任意中断都必定关闭连接并删除临时库及其 `-wal`/`-shm`。
  - 发布由稳定的 `.<index>.lock` 串行化。构建库先 `PRAGMA wal_checkpoint(TRUNCATE)`、再 `PRAGMA journal_mode=DELETE` 并关闭，校验 `-wal`/`-shm` 均不存在（自包含单文件）后，按“删除旧主库 → 删除旧 `-wal`/`-shm` 并校验 → `os.replace`”的顺序发布。
  - 任何中断点都不会出现 **[新主库 + 旧 WAL]**：若在删除旧主库后崩溃，`index_path` 缺失，下一次调用从原始 Trace 干净重建；`os.replace` 完成后磁盘上没有任何旧 sidecar，普通只读连接可安全打开该索引。
  - 僵尸临时库仅当 `tmp_db`、`tmp_db-wal`、`tmp_db-shm` 中所有存在文件的最新 mtime 均超过 `6` 小时，且能非阻塞取得其所有权锁（证明没有活跃构建）时才清扫；`PRAGMA journal_size_limit = 8388608` 限制的是 checkpoint 之后 WAL 文件的复用增长，**不是**活动事务期间的硬上限。
- **测试套件临时目录零残留（`tests/temp_workspaces.py`、`tests/conftest.py`）**：
  - 新增进程级临时工作区登记表：`nr4-probe-*` 双线程探测工作区、`mpr_` 短根以及 `mp_`、`mpc_`、`r6cas-`、`r6sup-`、`r7cas-`、`r10...-`、`nr_s6_r11root_` 等 `/tmp` 根统一登记。
  - 每个测试的 autouse fixture `finally` 与进程 `atexit` 双重兜底回收；只有 `shutil.rmtree` 之后确认 `not os.path.lexists(path)` 才从登记表移除，Windows 瞬时句柄占用会在下一次 `atexit` drain 重试。
- **回归测试（`tests/test_storage_lifecycle_contracts.py`）**：
  - 覆盖符号链接 `<root>/diff`、Windows reparse point（移除 `os.path.isjunction` 后由 `st_reparse_tag` / `FILE_ATTRIBUTE_REPARSE_POINT` 识别）与部分符号链接叶子绝不越界删除；确定性线程交错证明淘汰前重新核对，注册中的槽不会被删。
  - 同进程多线程 `cann_abi` 构建/淘汰不删除 `.cann_abi_build.lock`、不碰撞临时 `.so`；同进程多线程 Trace 重建使用唯一临时库；`>6h` 临时库在 `-wal` 仍新鲜或所有权锁被持有时不被清扫；故障注入证明发布中断后不会留下 [新主库 + 旧 WAL]，并覆盖临时工作区登记表的延迟重试。
