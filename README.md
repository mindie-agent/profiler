# `profiler` (`mindie_profiler` / `mindie-profiler`)

MindIE Agent 独立昇腾 NPU 性能剖析与跨运行对比仓库（`https://github.com/mindie-agent/profiler`），提供 `mindie-profiler`（等价于 `python3 -m mindie_profiler`）命令行入口，用于原地只读解析昇腾 Profiler 产物并输出结构化 `mindie-profile-summary/1`（C7 JSON）及跨运行对比回执：

```bash
# 安装
uv pip install git+https://github.com/mindie-agent/profiler@main

# 1. 原地分析 SQLite DB（或 kernel_details.csv），使用显式 step 窗口或无标签时间窗口
mindie-profiler \
  --root /path/to/ascend_pytorch_profiler_dir \
  --step-window 1=100000:250000 \
  --time-window 260000:400000 \
  --unit us --source auto \
  --mode inference --framework vllm-ascend --phase decode --tp 8 \
  --input-signature "qwen2.5-7b-bs16-in1024-out128" \
  --output /tmp/baseline-c7.json

# 2. 对比两次导出的 C7 摘要（或直接指定两侧 --{baseline,candidate}-root 与 --*-steps-file）
mindie-profiler compare \
  --baseline-summary /tmp/baseline-c7.json \
  --candidate-summary /tmp/candidate-c7.json \
  --output /tmp/compare-receipt.json
```
