# mindie-profiler 0.5.15

[中文](profiler-0.5.15.md)

This is a storage-lifecycle maintenance release. It fully preserves the `0.5.14` pairing with `mindie-sim 0.9.14`, CANN 9.x steady-state capture, the operator C-ABI catalog, content-addressed single-operator reproducers, cluster interconnect probes, and `ACLGraph` diagnostics. Every change only bounds disk caches, the content-addressed store, and temporary-directory leakage in long-running processes and the test suite; measurement semantics and receipt schemas are unchanged:

- **Bounded CANN 9.x capture-shim cache and compile-timeout cleanup (`mindie_profiler/cann_abi.py`)**:
  - `subprocess.TimeoutExpired` derives from `SubprocessError`, not `TimeoutError`, so the old code bypassed the timeout branch and leaked `.<shim>.tmp.<pid>`; compiler timeouts now surface as the builtin `TimeoutError`, and the unpublished temporary object is deterministically removed in `finally`, leaving only an object that was successfully `os.replace`d.
  - After a successful publish, only the newest `8` `libmindie_cann9_capture_*.so` variants survive by mtime, and the matching `.*.lock` files of evicted variants are removed with them. Interrupted `*.tmp.*` leaves older than `3600s` are swept; an `OSError` from a mapped or busy `.so` is ignored instead of downgrading the successful build.
- **Bounded `/tmp/mprof` content-addressed reproducer and diff retention (`mindie_profiler/repro_retention.py`)**:
  - Adds `prune_repro_storage(root, *, max_entries=64, max_age_days=14)` with independent count/age limits for CAS slots (`<sha>/repro.py` + `manifest.json`) and diff slots (`diff/<id>/diff.json`), so the short root (`MINDIE_REPRO_SHORT_ROOT`) cannot grow forever.
  - Strictly skips the process commit registry `_PROTECTED_INODES` (the committed component of `_protected_inodes()`), registered/active slots, lock-marked entries, symbolic links, and directories containing an unexpected payload. Eviction unlinks only known regular leaves before removing an empty directory, and every per-entry failure is best effort.
  - Runs opportunistically after each successful `stage_artifacts` delivery; a pruning failure never downgrades the delivered artifact to `delivery_failed`.
- **Atomic trace-sidecar rebuild and bounded WAL (`mindie_profiler/sources_trace.py`)**:
  - A rebuild writes a private `.<index>.tmp.<pid>` database and, after a clean close, publishes it together with its checkpointed `-wal`/`-shm`; a failure or parse interruption (including `ProfilerSchemaError`) removes the temporary database and its sidecars instead of leaving a half-built index.
  - Index connections set `PRAGMA journal_size_limit = 8388608` and run `PRAGMA wal_checkpoint(PASSIVE)` before close, so `.mindie-trace-index.sqlite3-wal` no longer grows with the trace; zombie build databases older than `6` hours are swept by the next build.
- **Zero leftover test temporary directories (`tests/temp_workspaces.py`, `tests/conftest.py`)**:
  - Adds a process-wide temporary-workspace registry covering `nr4-probe-*` two-thread probe workspaces, the `mpr_` short root, and the `mp_`, `mpc_`, `r6cas-`, `r6sup-`, `r7cas-`, `r10...-`, and `nr_s6_r11root_` `/tmp` roots.
  - A per-test autouse fixture `finally` and process `atexit` both reclaim them, so assertion failures, timeouts, and thread-startup errors leave nothing behind; `run_ranks` releases its own workspace immediately on an exceptional exit.
- **Regression tests (`tests/test_storage_lifecycle_contracts.py`)**:
  - Tier 0/1 coverage for compile-timeout temporary cleanup, the shim cache bound and stale-temporary sweep, CAS/diff age and count eviction with active-state protection, opportunistic pruning, failed sidecar cleanup and the WAL bound, and zero new `TMPDIR`/`/tmp` entries from `run_ranks`.
