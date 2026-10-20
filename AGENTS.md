# MindIE Profiler (`profiler`) — Agent Architecture Guide

Standalone repository (`https://github.com/mindie-agent/profiler`) for `mindie_profiler` (`mindie-profiler` CLI), providing in-place Ascend NPU profiler accounting (`ascend_pytorch_profiler_*.db`, `msprof_*.db`, `kernel_details.csv`), online HTTP profile-window control (`POST /start_profile`, `POST /stop_profile`), structured `mindie-profile-summary/1` (C7 JSON) projection, cross-run comparison (`mindie-profiler compare`), `P0–P4` HBM memory attribution, and read-only theoretical capacity bridging (`TensorCastAnalyticProvider` / `roofline-max-v1`).

See `mindie-agent/docs/profiler-system.md` for architecture and invariants.

## Verification Commands

```bash
pytest -q
```
