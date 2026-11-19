# MindIE Profiler (`profiler`)

`mindie-profiler` (`mindie_profiler` package, `mindie-profiler` / `mindie-profiler-api` CLI) owns controlled Ascend NPU profiling capture (CANN `msprof`, online `POST /start_profile` & `/stop_profile`, CANN 9.x MSPTI capture shim), in-place read-only SQLite/CSV/trace analysis (`inventory`, `analyze`, `correlate`, `compare`, `sql`, `camodel`, `kernels`), `P0–P4` HBM memory attribution, C-ABI operator inspection & sanitized single-op reproducer generation (`inspect-op-abi`, `repro-op`), 3-state topology alignment (`analyze --structure`), and read-only `mindie-sim` C7 measured-supply bridging (`sim_bridge*`).

- **Explicit Non-Ownership**: Causal discrete-event performance modeling, 4D efficiency decomposition, and SLA/PD Pareto sweeps belong to [`sim`](../sim); target CANN fault log triage and 3-primitive precision localization belong to [`debugger`](../debugger); MindIE Agent internal telemetry and opt-in Issue reporting belong to [`diagnostics`](../diagnostics).

---

## 1. Domain Invariants (`device-tool`)

1. **Zero Accidental NPU Context (`DEV-ZERO-CTX`)**:
   - Top-level package imports and offline analysis commands (`inventory`, `analyze`, `correlate`, `compare`, `sql`, `camodel`, `kernels`, `inspect-op-abi`, `repro-op`, `sim_bridge`) are pure CPU operations and must **never** import `torch_npu`, initialize CANN runtime contexts, or allocate HBM on `Phy-ID 0` (`0 MiB` HBM delta).
   - Live device probing (`fabric_probe`, `thermal_guard`, `collect`) runs only when explicitly invoked by the caller.
2. **In-Place Read-Only Analysis & Confined Staging (`DEV-READONLY-PATH`)**:
   - Offline analysis opens `ascend_pytorch_profiler_*.db` and `msprof_*.db` strictly read-only without mutating user profiling directories or polluting `cwd` / `$HOME`.
   - Trace sidecar indexes (`sources_trace.py`), CANN 9.x shim builds (`cann_abi.py`), and CAS reproducer slots (`repro_storage.py`, `repro_retention.py`) use atomic `os.replace` with symlink/NTFS-reparse-point rejection and bounded LRU/TTL eviction (`8` `.so` variants, `64` CAS/diff entries / `14d`).
   - Auxiliary retention or sidecar cleanup warnings after primary artifact delivery keep primary success intact (`Receipt Honesty`), and every `except OSError:` boundary is preceded by `except TimeoutError: raise`.
3. **3-State Topology Alignment, `mindie-sim` SSOT & Fresh Upstream Parity (`DEV-TOPOLOGY`)**:
   - Never duplicate model catalog geometry, Ascend SKU hardware peaks/topologies, observed operator/communication contracts, or closed-form subgraph FLOP/byte math inside `mindie_profiler`; delegate via PEP 562 `__getattr__` lazy shims to `mindie_sim.model_catalog`, `mindie_sim.backends.ascend.profiles()`, `mindie_sim.observed_contracts`, and `mindie_sim.subgraph_math`.
   - Structural mapping (`structure_mapping.py`, `structure_subgraphs.py`) preserves 3-state attribution (`matched`, `unmatched_observed`, `unobserved_declared`) on `mindie-model-structure/1` and A2 / A3 dual-Die / A5 (`Ascend950DT_*` / `Ascend950PR_9579` / `Ascend950PR_958b`) topology without fabricating silent 1:1 matches or `0.0` fallback latencies (`declared_only` / `unavailable` when cohorts or peaks are incomplete).
   - Verify fresh upstream `HEAD`s across the full Ascend stack (`vllm-ascend`, `cann-recipes-infer`, `MindIE-SD`, `cann/ops-transformer`, `cann/ops-nn`, `fla-npu`, `flash-attn-npu`, `cannbot-dsl`, `xllm` / `xllm-ops`, `torch-npu`) before updating operator normalization, `op_api_catalog.json`, or Advisor rules; cross-rank straggler and collective readiness accounting preserves explicit clock-alignment provenance (and CSV `--auto-step` requires real `Step Start Time(us)`).
4. **Bounded Memory, Clean-Core `mindie-sim` Bridge & Module Hygiene (`DEV-BOUNDED-MEM`)**:
   - Stream large JSON traces via `ijson`, scope multi-window PMU cache priming strictly to merged disjoint windows, and query SQLite slices in place (`<= 512 MiB` peak RSS; never whole-read traces `> 50 MiB`).
   - Bridge to `mindie-sim` strictly through public Clean-Core APIs (`sim_bridge*.py`) with zero deleted `opflow`/sidecar imports.
   - Keep every core module `< 800` lines with a top-30-line `[Role]` / `[Invariants]` / `[Timeouts & Locks]` / `[Side-Effect Policy]` docstring header, pass `scripts/check_no_magic_numbers.py`, and use Unix `LF` (`\n`) line endings.

---

## 2. Flat Sibling & Linked-Worktree Workflow

Keep primary checkouts on clean `main` and develop inside an isolated linked worktree under `../.worktrees/`:

```bash
git -C ../profiler fetch origin
git -C ../profiler worktree add -b feat/<topic> ../.worktrees/profiler-<topic> origin/main
cd ../.worktrees/profiler-<topic>
```

---

## 3. Verification Commands

```bash
# 1. Enforce Unix LF line endings and zero new magic-number debt
python3 .github/scripts/check_lf_eol.py
python3 -B scripts/check_no_magic_numbers.py \
  --root profiler=mindie_profiler \
  --baseline scripts/magic_number_baseline.json \
  --exceptions scripts/magic_number_exceptions.json

# 2. Prebuild mindie-sim C accelerator & run the maintained non-live-NPU suite
python3 -B -c "import mindie_sim.prediction.runtime.accel_build as b; b.build_accel()"
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. Validate PR body against the device-tool design-principles checklist
python3 .github/scripts/check_pr_checklist.py --profile device-tool --body-file <pr_body.md>
```

---

## 4. Living Specifications

- Architecture & profiler contract: [`../mindie-agent/docs/profiler-system.md`](../mindie-agent/docs/profiler-system.md)
- Workspace routing & guardrails: [`../mindie-agent/AGENTS.md`](../mindie-agent/AGENTS.md) and [`../mindie-agent/docs/historical-issues-and-guardrails.md`](../mindie-agent/docs/historical-issues-and-guardrails.md)
