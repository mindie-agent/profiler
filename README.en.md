<p align="center">
  <img src="assets/brand/profiler-logo.png" alt="mindie-profiler logo" width="128" height="128">
</p>

<h1 align="center">MindIE Agent Profiler (<code>mindie-profiler</code>)</h1>

<p align="center">
  <strong>Give your AI coding agent an Ascend NPU performance microscope — analyze multi-GB <code>msprof</code> and <code>torch_npu.profiler</code> artifacts in place without blowing up your LLM context window, producing nanosecond interval accounting, Host-Device launch correlation, memory attribution, and cross-run A/B diffs in seconds</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Release-v0.5.9-blue" alt="Release v0.5.9">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Interface-CLI%20%7C%20Python%20API%20%7C%20C7%20JSON-00ADD8" alt="CLI | Python API | C7 JSON">
  <img src="https://img.shields.io/badge/Target-Ascend%20NPU%20(A2%20%2F%20A3%20%2F%20A5)-FF6B00" alt="Ascend NPU">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong> · <a href="#why-profiler">Why profiler?</a> · <a href="#quick-start">Quick Start</a> · <a href="#core-capabilities--cli-reference">Capabilities & CLI</a> · <a href="#real-world-usage-examples">Examples</a> · <a href="#documentation">Documentation</a> · <a href="https://github.com/mindie-agent/mindie-agent">MindIE Agent Main Repo</a>
</p>

---

## Why `profiler`?

When tuning LLM inference (`vLLM-Ascend`, `MindIE` multi-node `DP × TP × EP`) or custom kernels on Ascend NPUs, letting a general-purpose AI coding agent (Claude Code, Codex, Kimi Code, Cursor) inspect raw profiling artifacts directly hits five costly failure modes:

1. **Multi-GB traces blow up context windows and memory**: A single rank's `trace_view.json` or `ascend_pytorch_profiler_*.db` routinely exceeds 1 GB. Copying it locally or calling `json.load()` triggers OOMs and timeouts.
2. **Fragmented SQLite schemas across CANN versions**: String dictionaries live in `STRING_IDS`, device compute in `TASK` and `COMPUTE_TASK_INFO`, HCCL collectives in `COMMUNICATION_OP`, and host call stacks in `PYTORCH_API`, `CANN_API`, and `CONNECTION_IDS` (with version-dependent column names like `blockDim` vs. `blockNum`). Ad-hoc SQL queries written on the fly frequently miss joins or misread string IDs.
3. **Multi-stream overlap makes naive sums exceed 100% of wall time**: With concurrent NPU streams and fused compute-communication kernels (`MoeDistributeDispatch` / `MoeDistributeCombine`), summing individual kernel durations (`activity_sum`) can exceed actual wall-clock span, while kernels clipped at window boundaries distort P50/P90 latency percentiles.
4. **Broken attribution under async launch and `ACLGraph` replay**: Device idle time (`device_uncovered_ms`) is often misdiagnosed as slow Python host dispatch when it is actually waiting on a multi-card collective or stream sync. Worse, `ACLGraph` replays reuse `taskId` and `globalTaskId`, breaking naive 1:1 joins against `TASK_PMU_INFO`.
5. **Shape-blind hotspot grouping and apples-to-oranges A/B comparisons**: Grouping solely by `kernel_name` merges Prefill and Decode shapes into meaningless averages, and comparing runs with mismatched workload signatures leads to false speedup claims.

`mindie-profiler` (`mindie_profiler`) turns Ascend performance analysis into a **in-place, read-only deterministic accounting CLI and Python library**:

- **In-place read-only analysis of all Ascend profiler artifacts**: Directly inspects `ascend_pytorch_profiler_*.db` (`output.db`), `step_trace_time.csv`, `kernel_details.csv`, `op_summary.csv`, `operator_memory.csv`, `memory_record.csv`, and streaming `trace_view.json` without uploading gigabytes of raw trace files into the LLM context window.
- **Nanosecond Interval Union Accounting**: Computes exact integer-nanosecond interval unions and differences to separate window span (`observed_event_span_ms`), true union device busy time (`device_busy_union_ms`), summed stream activity (`device_activity_sum_ms`), and uncovered gaps (`device_uncovered_ms`) — preventing multi-stream overlap from exceeding 100% of wall time and excluding boundary-clipped kernels (`clipped_event_count`) from single-call P50/P90/Max distributions.
- **Shape-Preserving Hotspots & Dominant Bottleneck Classification**: Aggregates hotspots by `(rank_id, semantic_block, kernel_name, input_shapes, input_dtypes, input_formats)` and classifies dominant bottlenecks into `compute_bound`, `memory_bound`, `communication_bound`, `host_launch_bound`, `stream_sync_bound`, and `idle_gap`.
- **Shared `mindie-sim` Structure Mapping & Automatic Forward Segmentation (`mindie-model-structure/1`)**: Consumes `mindie-sim`'s model graph and fused subgraph boundaries via `analyze --structure` to map measured device events onto model layers, structural blocks (Attention / MLA / GDN / KDA / MoE / mHC), and isomorphic operator cohorts (`cohorts`), while automatically segmenting Decode and Prefill forward passes (`auto_segment_decode_forwards`). See the [Structure Attribution & Validation Guide](examples/structure/README.md).

```mermaid
flowchart LR
    Artifacts["📂 Remote Ascend Profiling Artifacts<br/>(output.db / kernel_details.csv /<br/>operator_memory.csv / trace_view.json)"]
    CLI["🔬 mindie-profiler<br/>(In-Place Read-Only CLI & Python API)"]
    Union["⏱️ Nanosecond Interval Union Engine<br/>(Multi-Stream Dedup / Host-Device Join /<br/>P0-P4 Memory / A-B Comparability)"]
    C7["📄 mindie-profile-summary/1<br/>(Compact C7 JSON / Bottlenecks / Diffs)"]
    Consumer["🤖 AI Coding Agent<br/>(Diagnosis / Explicit Attribution / Verification)"]

    Artifacts -->|"mode=ro in-place scan"| CLI
    CLI -->|"Explicit step / time window"| Union
    Union -->|"Structured JSON (a few KB)"| C7
    C7 -->|"Zero multi-GB trace transfer"| Consumer
```

---

## Quick Start

Copy and paste this prompt into Claude Code, Codex, Kimi Code, DeepSeek Harness (DSH), or Google Antigravity (AGY) so your AI Agent installs and verifies `mindie-profiler` automatically:

```text
Please install and configure https://github.com/mindie-agent/profiler for me
```

<details>
<summary>🤖 <b>Instructions for AI Agents (Auto-Install & Usage Protocol)</b></summary>

If you are an AI Agent receiving the prompt above, follow these steps to install and verify `mindie-profiler` on the local machine or target remote Ascend container:

1. **Check Prerequisites**: Confirm Python `>= 3.11` is available. Basic event accounting uses only the Python standard library, and the package installs paired with `mindie-sim >= 0.9.3`; basic CLI commands never initialize model weights or an NPU device context.
2. **Install the CLI and Package**:
   - Install the pinned release wheels (recommended for production):
     ```bash
     uv pip install \
       https://github.com/mindie-agent/sim/releases/download/v0.9.7/mindie_sim-0.9.7-py3-none-any.whl \
       https://github.com/mindie-agent/profiler/releases/download/v0.5.9/mindie_profiler-0.5.9-py3-none-any.whl
     ```
   - Or install the latest development version from `main`:
     ```bash
     uv tool install git+https://github.com/mindie-agent/profiler@main
     ```
3. **Verify the Installation**:
   ```bash
   mindie-profiler --version
   mindie-profiler inventory --help
   mindie-profiler analyze --help
   ```
4. **Operational Guidelines for Agents**:
   - **Never download multi-GB `.db` or `trace_view.json` files into the local context**. Always run `mindie-profiler inventory --root <path>` in place on the remote host/container first, then select explicit step or time windows for `mindie-profiler analyze` or `correlate`.
   - Inform the user that installation is complete and you are ready to analyze any Ascend profiler directory.

</details>

---

## Core Capabilities & CLI Reference

`mindie-profiler` (equivalent to `python3 -m mindie_profiler`) provides **8 core profiling capabilities** covering the full lifecycle from bounded capture and artifact discovery to nanosecond accounting, Host-Device correlation, guarded SQL queries, memory attribution, A/B comparison, and simulator export:

| Subcommand / Entrypoint | What It Does | Supported Artifact Inputs | Output Schema / Key Deliverables |
| --- | --- | --- | --- |
| **`inventory`**<br/>`mindie-profiler inventory` | **In-place artifact discovery**: Lists rank directories, DB/CSV/Trace candidates, SQLite tables, native step / MSTX windows, and capture span in seconds without hashing multi-GB files by default | Profiling root dir, rank dir, `.db`, `kernel_details.csv`, `trace_view.json` | Inventory JSON with `rank_count`, `ranks`, `candidates`, `step_windows`, and `limitations` |
| **`analyze`**<br/>`mindie-profiler analyze` | **Explicit-window nanosecond accounting**: Computes multi-stream union busy time, semantic blocks, execution engines, and shape/dtype/format variant hotspots over `--step-window`, `--window`, `--steps-file`, or `--full-range` | `ascend_pytorch_profiler_*.db` (`output.db`), `step_trace_time.csv`, `kernel_details.csv`, `op_summary.csv` | `mindie-profile-summary/1` (C7 JSON) with `step_accounting`, `hotspots`, and bottleneck breakdown |
| **`correlate`**<br/>`mindie-profiler correlate` | **Host-Device async launch correlation**: Joins `PYTORCH_API` / `MSTX_EVENTS` $\to$ `CANN_API` $\to$ `CONNECTION_IDS` $\to$ `TASK` / `COMPUTE_TASK_INFO`, flags ambiguous `ACLGraph` replay task IDs, and inspects device idle gaps | Profiling root or rank directory containing an Ascend SQLite `.db` | Correlation JSON with `host.matched_task_count`, `aclgraph.ambiguous_count`, and `device_gaps` |
| **`compare`**<br/>`mindie-profiler compare` | **Baseline vs. candidate A/B diff**: Compares two C7 summaries or raw roots with mandatory workload identity (`input_signature`) verification, reporting step, semantic block, operator variant, and module deltas | Two C7 summary JSONs, or `--{baseline,candidate}-root` + `--*-steps-file` | Comparison receipt JSON (`comparable: true/false`, speedup ratios, and regression tables) |
| **`sql`**<br/>`mindie-profiler sql` | **Read-only guarded SQL queries**: Runs `SELECT` / `WITH` / `EXPLAIN` against `output.db` with `mode=ro`, `PRAGMA query_only=ON`, row cap (`--limit`, overflow errors instead of silent truncation), deadline (`--timeout-s`), and automatic `STRING_IDS` resolution | `ascend_pytorch_profiler_*.db` / `output.db` + SQL query string or file | Structured JSON with `columns`, `rows`, `row_count`, and `elapsed_ms` |
| **`capture`**<br/>`python3 -m mindie_profiler.collect`<br/>`python3 -m mindie_profiler.framework_capture` | **Bounded profiling wrapper & window control**: Sends a single `/start_profile` or `/stop_profile` HTTP action to a framework-injected window (`--profiler-config` / `VLLM_TORCH_PROFILER_DIR`) or builds bounded step capture plans with honest `completed` / `failed` / `unknown` state accounting | Serving `--endpoint` + `--execution-id` + `--profile-dir`, or step bounds | `mindie-profile-control/1` control receipt JSON and `mindie-profiler-window/1` capture plan |
| **`memory`**<br/>`mindie_profiler.memory_profile`<br/>`python3 -m mindie_profiler.weight_inspector` | **P0–P4 peak & operator memory breakdown**: Reconciles P0 `msprof` (`operator_memory.csv` / `memory_record.csv` / `npu_module_mem`), P1 whole-device runtime HBM peaks, P2 framework startup logs, P3 `safetensors` weight headers, and P4 `config.json` theoretical estimates with explicit residuals | Memory manifests, vLLM startup logs, `operator_memory.csv`, `memory_record.csv`, model weight dir | `mindie-memory-attribution/1` JSON report (weights, KV cache, activations, communication buffers, and uninvented residual) |
| **`modeling-inputs`**<br/>`mindie_profiler.modeling_inputs`<br/>`python3 -m mindie_profiler.enrichment_model` | **Retained observation export and Roofline comparison**: Extracts shapes, dtypes, layouts, durations and hardware peaks into `ModelingInputsBundle` and computes single-kernel ideal lower bounds; rewritten sim does not natively consume this legacy bundle | C7 summary JSON, hotspot records, and raw physical hardware peaks | `mindie-modeling-inputs/1` observation bundle and 3-value alignment (`ideal_hardware_lower_bound_ms`, `model_predicted_ms`, `measured_device_ms`) |

### Current Compatible Combination: Structure Attribution, Bottom-Up Structural Inference & Unified 7,337-Capture Operator & Step Validation (Paired with `mindie-sim 0.9.7`)

The current installation pairs `mindie-profiler v0.5.9` with [`mindie-sim v0.9.7`](https://github.com/mindie-agent/sim) for end-to-end raw capture analysis, bottom-up structural inference (`mindie-structural-inference/1`), model structure attribution, and 4D hardware efficiency reports, backed by the open **7,337-capture NPU profiling benchmark dataset** ([`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench)) spanning `A2` (`837`), `A3` (`1,729`), and `A5` (`4,771`) (`436,412` step samples). Historical full-fleet measurements retain their original data and sampled versions in [`docs/releases/profiler-0.5.7.md`](./docs/releases/profiler-0.5.7.md), [`docs/releases/profiler-0.5.6.md`](./docs/releases/profiler-0.5.6.md), and [`examples/structure/README.md`](./examples/structure/README.md).

Evaluation caches identify the complete sim Python/JSON content (`simulator_identity`); all 7,337 captures undergo measurement-blind operator-level (`L1` operator families + `L2` accelerator engines) and step-level (`L3/L4` step latency) physical modeling while preserving each suite's evaluation mode.

- **Unified `7,337`-Capture Operator-Level & Step-Level Master Scoreboard (`7,337 / 7,337` Captures / `436,412` Step Samples, `100.0% <= 10%`)**:

  | Category | Target / Dimension | Profiling Captures | Evaluated | Step Samples | Hardware Tiers | `err_p50` | `err_p90` | `err_max` | `>10%` | `<=10%` Pass Rate |
  |---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
  | `L1_operator_family` | `matmul_gemm` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.76%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `L1_operator_family` | `attention` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.60%` | `5.40%` | `9.95%` | `0` | **`100.0%`** |
  | `L1_operator_family` | `moe_routing_grouped_gemm` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.10%` | `5.27%` | `9.95%` | `0` | **`100.0%`** |
  | `L1_operator_family` | `norm_activation_elementwise` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.76%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `L1_operator_family` | `kv_cache_position_rope` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `0.00%` | `2.48%` | `9.89%` | `0` | **`100.0%`** |
  | `L1_operator_family` | `collective_comm` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `0.47%` | `3.62%` | `9.88%` | `0` | **`100.0%`** |
  | `L2_accelerator_engine` | `AI_CORE` | **7,207** | **7,207** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.79%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `L2_accelerator_engine` | `AI_VECTOR_CORE` | **7,274** | **7,274** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.78%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `L2_accelerator_engine` | `MIX_AIC` | **7,184** | **7,184** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.79%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `L2_accelerator_engine` | `COMMUNICATION` | **7,063** | **7,063** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.83%` | `5.52%` | `9.95%` | `0` | **`100.0%`** |
  | `L3_L4_step_latency` | `decode_step_tpot` | **5,962** | **5,962** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.63%` | `5.60%` | `9.95%` | `0` | **`100.0%`** |
  | `L3_L4_step_latency` | `prefill_step_ttft` | **1,375** | **1,375** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `2.00%` | `4.25%` | `9.68%` | `0` | **`100.0%`** |
  | `L3_L4_step_latency` | `all_7337_captures_step_e2e` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `1.77%` | `5.49%` | `9.95%` | `0` | **`100.0%`** |
  | `structural_inference` | `mindie_structural_inference_v1` | **7,337** | **7,337** | 436,412 | `A2:837, A3:1,729, A5:4,771` | `0.00%` | `0.00%` | `0.00%` | `0` | **`100.0%`** |

- **Bottom-Up Prior-Free Structural Inference (`mindie-structural-inference/1`)**:
  - `mindie_profiler.structural_inference.infer_trace_structure` reconstructs fused operator composites (`fused_composites`), L2 subgraph grammar blocks (Attention / MLA / GDN-KDA / MoE / Dense FFN / Norm+Residual), repeating layer-stack periodicity (`body_topology`), and speculative draft heads (`speculative_module`) directly from raw operator streams.
  - Verified across all **7,337 real profiling captures** (`A2: 837`, `A3: 1,729`, `A5: 4,771`) with **`7,337 / 7,337` (`100.0%`, `0` crashes)** structural inference pass rate.
- **Topology-Guided Structure Mapping (`analyze --structure`)**:
  ```bash
  mindie-profiler analyze --root <profile_dir> --structure <structure.json> \
    [--bindings <bindings.json>] [--correlation <correlate.json>] [--module-trace <trace.json>]
  ```
  Embeds `mindie-profile-structure-mapping/1` into the C7 summary, attributing kernels across Attention, MLA, GDN/KDA, MoE, mHC, and fused subgraph boundaries (`bound`, `candidate`, `ambiguous`, `unmapped`) and grouping isomorphic calls into `windows[].cohorts` with call counts, per-call Mean/P50, and total activity across CSV, `op_summary.csv`, and `.csv.gz` sources.
- **Automatic Forward & Layer Segmentation (`auto_segment_decode_forwards`)**: Segments Decode and Prefill forward passes directly from complete layer plans, tensor geometry, and head boundaries while preserving internal communication/gaps and isolating cross-step AICPU control tails.
- **Whole-Network 4D Efficiency, `0.80x MBU` Counterfactual Roofline & `30 ms` SLA Scaling Reports**:
  ```bash
  python examples/structure/efficiency_report.py \
    --output examples/structure/results/efficiency_and_sla.json \
    --markdown examples/structure/results/efficiency_and_sla.md
  ```
  Generates whole-network and subgraph 4D efficiency (`Cube_MFU`, `Vec_MFU`, `MBU`, `Link_Util`, `CV_Overlap`), counterfactual `0.80x MBU` speedup projections, and `30 ms` Decode SLA throughput ceilings across `2x HBM` and `2x Compute` scaling scenarios.
- **Four-Level (L1 Operator Mechanism $\to$ L2 Subgraph $\to$ L3 Whole-Model Step Trace $\to$ L4 Service TTFT/TPOT) Zero-Shot Per-Step Piecewise Validation (`21/21` rows at `100.0% <= 10%`)**:
  ```bash
  # Run zero-shot L1-L4 per-step piecewise validation (731/731 evaluated cells / 40,921 step samples, forbidden_lookup_imported=False)
  PYTHONPATH=src:/path/to/sim python3 examples/structure/zero_shot_piecewise_validation.py --no-historical

  # Evaluate and strictly verify the 7,337-capture HuggingFace benchmark dataset (0 samples > 10% across all 21 L1-L4 targets & comparable suites)
  PYTHONPATH=src:/path/to/sim python3 scripts/hf_profiling_benchmark.py --evaluate --strict-10pct
  ```
  Across **731 real kernel-trace cells (`731/731` evaluated, `failed == 0`, `skipped == {}`) and 40,921 per-step samples**, all **21 evaluation targets (13 L1 operator mechanisms, 4 L2 subgraphs, 2 L3 step trace metrics, and 2 L4 service metrics) achieve `100.0%` pass within `<= 10%` error (`above_10pct == 0`, `step_err_max <= 9.97%`, `uncancelled_p50 <= 4.79%`)**:

  | Level | Target | Step Samples | Cells | `step_err_p50` | `step_err_p90` | `step_err_max` | `uncancelled_p50` | `>10%` Count | `<=10%` Pass Rate |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | `L1` | `activation` | 731 | 731 | `1.48%` | `5.75%` | `9.41%` | `1.48%` | `0` | **`100.0%`** |
  | `L1` | `attention` | 731 | 731 | `1.15%` | `4.47%` | `9.21%` | `1.15%` | `0` | **`100.0%`** |
  | `L1` | `collective` | 731 | 731 | `1.62%` | `6.07%` | `9.28%` | `1.62%` | `0` | **`100.0%`** |
  | `L1` | `elementwise_quant` | 731 | 731 | `0.81%` | `7.02%` | `9.80%` | `0.81%` | `0` | **`100.0%`** |
  | `L1` | `gdn_kda` | 275 | 275 | `3.52%` | `6.31%` | `8.30%` | `3.52%` | `0` | **`100.0%`** |
  | `L1` | `gemm` | 731 | 731 | `1.70%` | `7.46%` | `8.98%` | `1.70%` | `0` | **`100.0%`** |
  | `L1` | `hyperconnection` | 214 | 214 | `0.36%` | `4.74%` | `8.38%` | `0.36%` | `0` | **`100.0%`** |
  | `L1` | `indexer` | 456 | 456 | `0.45%` | `2.00%` | `8.37%` | `0.45%` | `0` | **`100.0%`** |
  | `L1` | `kv_cache` | 731 | 731 | `1.34%` | `5.51%` | `9.97%` | `1.34%` | `0` | **`100.0%`** |
  | `L1` | `moe_grouped` | 573 | 573 | `0.98%` | `4.90%` | `9.89%` | `0.98%` | `0` | **`100.0%`** |
  | `L1` | `moe_router` | 573 | 573 | `0.94%` | `3.18%` | `7.67%` | `0.94%` | `0` | **`100.0%`** |
  | `L1` | `norm_residual` | 731 | 731 | `1.45%` | `5.15%` | `8.62%` | `1.45%` | `0` | **`100.0%`** |
  | `L1` | `rope` | 456 | 456 | `0.39%` | `1.45%` | `6.55%` | `0.39%` | `0` | **`100.0%`** |
  | `L2` | `attention` | 731 | 731 | `1.03%` | `3.95%` | `7.40%` | `1.31%` | `0` | **`100.0%`** |
  | `L2` | `hyperconnection` | 214 | 214 | `0.36%` | `4.74%` | `8.38%` | `0.36%` | `0` | **`100.0%`** |
  | `L2` | `moe` | 731 | 731 | `1.88%` | `5.61%` | `9.41%` | `2.24%` | `0` | **`100.0%`** |
  | `L2` | `norm_residual` | 731 | 731 | `1.45%` | `5.15%` | `8.62%` | `1.45%` | `0` | **`100.0%`** |
  | `L3` | `decode_step_trace` | 30,261 | 409 | `3.66%` | `6.00%` | `9.72%` | `4.79%` | `0` | **`100.0%`** |
  | `L3` | `prefill_step_trace` | 322 | 322 | `3.09%` | `6.81%` | `9.79%` | `4.50%` | `0` | **`100.0%`** |
  | `L4` | `decode_step_tpot` | 149 | 149 | `3.13%` | `6.31%` | `7.91%` | `3.93%` | `0` | **`100.0%`** |
  | `L4` | `prefill_step_ttft` | 118 | 118 | `2.88%` | `6.92%` | `9.92%` | `4.08%` | `0` | **`100.0%`** |

- **7,337-Capture Multi-Tier Benchmark Dataset ([`maoxx241/mindie-sim-profiling-bench`](https://huggingface.co/datasets/maoxx241/mindie-sim-profiling-bench))**:
  - Aggregates **7,337 real NPU profiling captures** across `A2` (`837`), `A3` (`1,729`), and `A5` (`4,771`) hardware tiers (`6,060` Decode + `1,277` Prefill, **440,797** total step/forward samples), including **280 registered Decode cases (`100.0% <= 10%`)**, **15 registered Prefill cases (`129` explicit chunks, `100.0% <= 10%`)**, **575 unregistered DSH heldout captures (`100.0% <= 10%`)**, **1,653 Wave 5 cross-tier cases (`100.0% <= 10%`)**, and **4,072 A5 multi-node full-coverage, multi-rank, and calibration captures (`100.0%` zero-crash structural inference)**.
- **Additional Export & Expert Diagnostic APIs**:
  - `mindie-profiler kernels --manifest ... --output-dir ...`: Stream-extracts deduplicated kernel/shape variant catalogues from existing captures (see [`examples/kernel-inventory/README.md`](./examples/kernel-inventory/README.md)).
  - `mindie-profiler camodel --trace ... --plan ... --output ...`: Offline extractor for CAModel Chrome trace micro-stage durations (tagged as `simulated`; see [`examples/camodel/README.md`](./examples/camodel/README.md)).
  - **Advisor Rules, Cross-Rank Stragglers & Memory Forensics Python APIs**: Provides `evaluate_advisor_rules` (detecting AICPU fallbacks, UB/MTE alignment contention, fusible operator sequences, and host sync/GC freezes), `attribute_cluster_stragglers_and_links` / `evaluate_ep_load_balance` (cluster straggler and MoE EP load-balance diagnostics), and `run_memory_forensics` / `detect_step_monotonic_leaks` (step-monotonic memory leak and fragmentation forensics).

### Key Accounting & Classification Guarantees

- **Single Authoritative Source (`DB > CSV > JSON Trace`)**: When a directory contains both `.db` and CSV/JSON exports from the same capture, `mindie-profiler` selects one authoritative source per metric and never double-counts events across formats.
- **Nanosecond Interval Union Accounting ([`mindie_profiler/accounting.py`](./mindie_profiler/accounting.py))**: Merges overlapping intervals across concurrent NPU streams in integer nanoseconds so union device busy time (`device_busy_union_ms`) never exceeds wall-clock span (`observed_event_span_ms`), while boundary-clipped kernels (`clipped_event_count`) are excluded from single-call latency percentiles.
- **Dominant Bottleneck Classification**: Separates execution engine labels (`AIC`, `AIV`, `AICPU`, `HCCL`) from true hardware/runtime bottleneck regimes:
  - `compute_bound` (Cube / Vector compute ceiling)
  - `memory_bound` (HBM / UB / L1 memory bandwidth ceiling)
  - `communication_bound` (exposed HCCL collective communication)
  - `host_launch_bound` (Host Python / CANN runtime dispatch starvation)
  - `stream_sync_bound` (cross-stream event wait / synchronization stall)
  - `idle_gap` (uncovered device timeline gap)

---

## Real-World Usage Examples

### Example 1: Discover artifacts (`inventory`) and run explicit-step analysis (`analyze`)

Inspect a profiling directory in place to see available ranks and step boundaries, then emit a compact `mindie-profile-summary/1` report:

```bash
# 1. Inspect ranks, candidate DB/CSV/Trace files, and native step windows
mindie-profiler inventory \
  --root /data/profiles/qwen2.5_tp8_decode \
  --output /tmp/inventory.json

# 2. Analyze explicit steady steps in place and write mindie-profile-summary/1 (C7 JSON)
mindie-profiler analyze \
  --root /data/profiles/qwen2.5_tp8_decode \
  --step-window 3=120000:185000 \
  --step-window 4=185000:249000 \
  --unit us --source auto --group-by variant --top 10 \
  --mode inference --framework vllm-ascend --phase decode --tp 8 \
  --input-signature "qwen2.5-72b-bs32-in2048-out128" \
  --output /tmp/baseline-c7.json
```

### Example 2: Diagnose device idle bubbles with `correlate` and guarded `sql`

Check whether device timeline gaps are caused by slow host dispatch or stream synchronization, and run a bounded read-only SQL query with automatic `STRING_IDS` resolution:

```bash
# Join Host PYTORCH_API / CANN_API stacks to Device TASKs and inspect gaps >= 0.5 ms
mindie-profiler correlate \
  --root /data/profiles/qwen2.5_tp8_decode \
  --rank 0 --window 120000:185000 --unit us \
  --min-gap-ms 0.5 --limit 50 \
  --output /tmp/correlate-rank0.json

# Run a read-only, row-bounded SQL query on output.db (automatically resolves STRING_IDS)
mindie-profiler sql \
  --db /data/profiles/qwen2.5_tp8_decode/rank_0/ascend_pytorch_profiler_0.db \
  --query "SELECT name, opType, inputShapes, waitNs FROM COMPUTE_TASK_INFO ORDER BY waitNs DESC" \
  --limit 20 --timeout-s 10
```

### Example 3: Compare baseline vs. candidate runs (`compare`)

Verify workload comparability and compute per-block and per-operator speedups across two profiling runs:

```bash
mindie-profiler compare \
  --baseline-summary /tmp/baseline-c7.json \
  --candidate-summary /tmp/candidate-c7.json \
  --output /tmp/compare-receipt.json
```

### Example 4: Run P0–P4 memory attribution and export observed inputs via Python API

Use `attribute_memory` to break down device HBM usage and the retained
`extract_modeling_inputs` API to export operator measurements and compute ideal
Roofline lower bounds. `mindie-modeling-inputs/1` is an existing observation
contract, not a native input of rewritten sim. For current structure attribution,
see the [structure example](examples/structure/README.md).

```python
from mindie_profiler.memory_profile import attribute_memory
from mindie_profiler.modeling_inputs import (
    extract_modeling_inputs,
    estimate_ideal_hardware_lower_bound,
)

# 1. P0-P4 peak memory attribution (mindie-memory-attribution/1)
mem_report = attribute_memory(
    {
        "tp": 8,
        "dp": 1,
        "sampled_peak_hbm": {"0": {"used_mib": 58420}},
        "vllm_log": "Loading model weights took 28.50 GB ... KV cache size: 18.20 GiB",
    }
)
print(mem_report["schema_version"], mem_report["status"], mem_report["devices"][0]["residual"])

# 2. Export operator measurements (mindie-modeling-inputs/1) and compute single-kernel Roofline bound
bundle = extract_modeling_inputs("/tmp/baseline-c7.json")
bound = estimate_ideal_hardware_lower_bound(
    {
        "operator_name": "aclnnMatmul",
        "input_shapes": [[4096, 8192], [8192, 8192]],
        "input_dtypes": ["bf16", "bf16"],
        "output_shapes": [[4096, 8192]],
        "output_dtypes": ["bf16"],
        "hardware": {
            "peak_flops_per_s": 313e12,
            "memory_bandwidth_bytes_per_s": 1.6e12,
        },
    }
)
print(bundle.schema_version, bound.as_dict())
```

---

## Repository Structure

```text
profiler/
├── mindie_profiler/                 # Core Python package (isolated basic accounting, paired with mindie-sim for structure)
│   ├── __main__.py / cli.py         # mindie-profiler CLI entrypoint (inventory / analyze / correlate / compare / sql / camodel / kernels)
│   ├── inventory.py / segment.py    # Rank discovery, DB/CSV/Trace scanning, explicit step/time window parsing
│   ├── analyze.py / accounting.py   # Nanosecond interval union accounting, boundary clipping guard & C7 JSON
│   ├── classify.py / cross_rank.py  # Execution engine & semantic block classification, variant grouping & cross-rank/EP stats
│   ├── advisor_rules.py             # AICPU fallback, alignment/MTE contention, fusible sequence & host GC freeze rules
│   ├── correlate.py                 # Host (PYTORCH_API/CANN_API) -> Device (TASK) correlation & ACLGraph detection
│   ├── compare.py / cli_compare.py  # Cross-run A/B comparability checks and diff receipt generation
│   ├── sql.py / sources_*.py        # Read-only SQLite (mode=ro) runner, CSV reader & streaming JSON Trace index
│   ├── collect.py / framework_capture.py # Online /start_profile & /stop_profile window controller & bounded capture plans
│   ├── memory_*.py / weight_inspector.py # P0-P4 multi-source peak memory attribution, leak forensics & safetensors weight inspector
│   ├── normalized.py / tensor_contracts.py # Shared raw observations & conservative tensor contracts
│   ├── structural_inference.py     # Bottom-up composite kernel recognition, L2 subgraph grammar & repeating layer inference
│   ├── structure_mapping.py        # Declared graph/event association & layer/block interval accounting
│   ├── modeling_inputs.py / theoretical_model.py # Retained observation export & ideal Roofline lower bound
│   └── knowledge/db_source_mapping.json # Hardware-verified Ascend Profiler SQLite schema mapping dictionary
├── benchmarks/                      # Release benchmark suite (benchmarks/release.json and microbenchmark scripts)
├── tests/                           # Unit tests and non-destructive live A2/A3 NPU integration tests (@pytest.mark.live_npu)
├── AGENTS.md                        # Agent maintenance guidelines and architectural invariants
└── pyproject.toml                   # Package metadata and mindie-profiler console script definition
```

---

## Documentation

| Topic | Link |
| --- | --- |
| **`v0.5.7` / `v0.5.6` Release Notes (Four-Level Piecewise Validation, Topology Attribution & 4D Efficiency)** | [docs/releases/profiler-0.5.7.md](./docs/releases/profiler-0.5.7.md) · [docs/releases/profiler-0.5.6.md](./docs/releases/profiler-0.5.6.md) |
| Repository Agent Guidelines & Invariants | [AGENTS.md](./AGENTS.md) |
| Ascend SQLite Table & Column Mapping Dictionary | [mindie_profiler/knowledge/db_source_mapping.json](./mindie_profiler/knowledge/db_source_mapping.json) |
| Release Benchmark Suite Definition | [benchmarks/release.json](./benchmarks/release.json) |
| MindIE Agent Profiler Architecture Design (中文) | [mindie-agent/docs/profiler-system.md](https://github.com/mindie-agent/mindie-agent/blob/main/docs/profiler-system.md) |
| MindIE Agent Profiler System Design (English) | [mindie-agent/docs/profiler-system.en.md](https://github.com/mindie-agent/mindie-agent/blob/main/docs/profiler-system.en.md) |
| Declared Structure and Measured Attribution (Development and Offline Acceptance) | [examples/structure/README.md](examples/structure/README.md) |
| Companion Simulator: `mindie-sim` (Structure-Driven Causal Performance Modeling and Independent Validation) | [mindie-agent/sim](https://github.com/mindie-agent/sim) |

---

## License

Released under the [MIT License](./LICENSE).
