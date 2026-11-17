# mindie-profiler 0.5.16：清理历史旁路死代码、对齐 Clean-Core `mindie-sim 0.9.18` 桥接与 `device-tool` 治理

[English](profiler-0.5.16.en.md)

`mindie-profiler v0.5.16` 完成与 Clean-Core `mindie-sim v0.9.18` 的正式标签绑定、旁路死代码清理及 `device-tool` 贡献门禁对齐：

- **移除历史旁路模块与对齐 Clean-Core `mindie-sim v0.9.18`**：清理历史遗留的死代码旁路与冗余兼容分支，`sim_bridge*.py` 与 `tensor_cast_provider.py` 全面切换至 `mindie-sim v0.9.18` 唯一因果主干公开接口，并将 `pyproject.toml` 中的 `mindie-sim` 依赖升级锁定至 `mindie-sim v0.9.18` 正式不可变 Git 标签提交。
- **测试加速与 `< 800` 行内聚模块治理**：精简重复构建开销以显著提速跨平台 CI（Linux / macOS / Windows），保持全部核心模块 `< 800` 行、顶部四段式契约头与流式低内存边界（`<= 512 MiB`）。
- **`device-tool` 贡献指南与 PR 门禁对齐**：完善 `AGENTS.md`、双语 `CONTRIBUTING{.en}.md`、`.github/pull_request_template.md` 与 `--profile device-tool` PR 设计原则校验门禁。
