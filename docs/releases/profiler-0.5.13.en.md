# mindie-profiler 0.5.13

[中文](profiler-0.5.13.md)

Paired with [`mindie-sim 0.9.13`](https://github.com/mindie-agent/sim/releases/tag/v0.9.13), this release hardens Windows `CP936` / `CREATE_NO_WINDOW` child-pipe handling, WSL2 native executable resolution against `/mnt/c` `.exe` / DrvFS shadowing, and `TimeoutError` propagation across capture and inventory boundaries.

- **Windows Process-Tree Cleanup & `CP936` UTF-8 Pipe Discipline**: `vllm_online_evidence.terminate_process_group` now terminates Windows process trees cleanly via windowless `taskkill /T /F /PID` instead of POSIX-only `os.getpgid` / `SIGKILL`, and child Python subprocesses run with `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` paired with explicit UTF-8 pipe decoding.
- **WSL2 Native Binary Lookup & `\\?\` Git Path Normalization**: Added `_host_exec.which_native` and `normalize_git_repo_arg` so `git` and compiler invocations on WSL2 skip symlinked or direct `/mnt/c` DrvFS / PE binaries, and standard-length `\\?\` paths are normalized before invoking `git -C` on Windows.
- **Honest `TimeoutError` Propagation**: Added explicit `except TimeoutError: raise` guards ahead of `OSError` handlers across `cann_abi`, `kernel_inventory`, `native_capture`, `native_capture_shm`, and `stat()`-backed executable checks.
