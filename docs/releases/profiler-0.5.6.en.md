# mindie-profiler 0.5.6

[中文](profiler-0.5.6.md)

## Profiler-to-Sim Reverse Calibration Bridge & First-Class xLLM / MindIE-SD Framework Support

- **Profiler-to-Sim Reverse Calibration Bridge (`mindie_profiler/sim_bridge.py`)**:
  - Add `export_sim_calibration` and `export_sim_case` to export measured `msprof` profile summaries, operator-family latency breakdowns, and multi-rank communication statistics directly into `mindie-sim` calibration payloads and deterministic Case specs, wired into the CLI entry point.
- **First-Class xLLM and MindIE-SD Collection & Memory Log Parsing**:
  - Extend `mindie_profiler/collect.py`, `mindie_profiler/framework_capture.py`, `mindie_profiler/memory_logs.py`, and `mindie_profiler/memory_profile.py` with first-class controlled collection, framework capture, and memory-pool log analysis for `xllm` and `mindie-sd` (`mindiesd`) workloads.
