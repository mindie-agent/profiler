# mindie-profiler 0.5.13

[English](profiler-0.5.13.en.md)

本版本配套正式发布的 [`mindie-sim 0.9.13`](https://github.com/mindie-agent/sim/releases/tag/v0.9.13)，完成 Windows `CP936` / `CREATE_NO_WINDOW` 子进程管道编码、WSL2 原生工具链防 `.exe` / DrvFS 遮蔽以及全链路 `TimeoutError` 传播加固。

- **Windows 进程树清理与 `CP936` UTF-8 管道对齐**：`vllm_online_evidence.terminate_process_group` 在 Windows 上使用无窗口 `taskkill /T /F /PID` 替代仅限 POSIX 的 `os.getpgid` / `SIGKILL`；Python 子进程导出与分析统一注入 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` 并以 UTF-8 解码输出，避免中文 OEM `CP936` 主机管道乱码或异常崩溃。
- **WSL2 原生可执行文件发现与 `\\?\` Git 路径规范化**：新增 `_host_exec.which_native` 与 `normalize_git_repo_arg`，在 WSL2 上通过符号链接解析与 `/proc/self/mountinfo` / PE 头校验跳过 `/mnt/c` Windows 可执行文件遮蔽，并在 Windows 上剥离常规长度 `\\?\` 前缀以兼容 Git for Windows `-C`。
- **异常边界诚实传播**：在 `cann_abi`、`kernel_inventory`、`native_capture`、`native_capture_shm` 与 `_host_exec` 的全部 `OSError` 捕获点前显式透传 `TimeoutError`（含基于 `stat()` 的文件探测，避免 `Path.is_file()` 静默吞没超时）。
