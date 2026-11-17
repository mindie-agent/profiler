# mindie-profiler 0.5.16: Dead-Sidecar Purge, Clean-Core `mindie-sim 0.9.18` Bridge Alignment, and `device-tool` Governance

[中文](profiler-0.5.16.md)

`mindie-profiler v0.5.16` aligns with the Clean-Core `mindie-sim v0.9.18` formal release, removes legacy dead sidecars, and completes `device-tool` contributor governance:

- **Dead-Sidecar Purge & Formal `mindie-sim v0.9.18` Pin**: Purges obsolete sidecar modules and compatibility shims, aligns `sim_bridge*.py` and `tensor_cast_provider.py` with `mindie-sim v0.9.18` Clean-Core APIs, and pins `mindie-sim` in `pyproject.toml` to the immutable `v0.9.18` release commit.
- **CI Acceleration & Sub-800-Line Module Hygiene**: Eliminates redundant per-worker setup overhead across Linux/macOS/Windows CI while keeping all core modules `< 800` lines with 4-part invariant headers and bounded streaming I/O (`<= 512 MiB`).
- **`device-tool` Governance Alignment**: Adds comprehensive `AGENTS.md`, bilingual `CONTRIBUTING{.en}.md`, `.github/pull_request_template.md`, and `--profile device-tool` PR checklist validation.
