# MindIE Profiler (`profiler`)

`mindie-profiler` (`mindie_profiler` package, `mindie-profiler` / `mindie-profiler-api` CLI) owns controlled Ascend NPU profiling capture (CANN `msprof`, online `POST /start_profile` & `/stop_profile`, CANN 9.x MSPTI capture shim), in-place read-only SQLite/CSV/trace analysis (`inventory`, `analyze`, `correlate`, `compare`, `sql`, `camodel`, `kernels`), `P0–P4` HBM memory attribution, C-ABI operator inspection & sanitized single-op reproducer generation (`inspect-op-abi`, `repro-op`), bounded multi-tier HCCL fabric calibration (`fabric-probe`), the standalone incremental silicon benchmark suite (`bench {abi,run-plan,diff,sku,subgraph,pr-ab}`), 3-state topology alignment (`analyze --structure`), and read-only `mindie-sim` C7 measured-supply & native-call bridging (`sim_bridge.py`, `sim_native_bridge.py`, `sim_structure_ingress.py`, `sim_draft_geometry.py`).

- **Explicit Non-Ownership**: Causal discrete-event performance modeling, 4D efficiency decomposition, and SLA/PD Pareto sweeps belong to [`sim`](../sim); target CANN fault log triage and 3-primitive precision localization belong to [`debugger`](../debugger); MindIE Agent internal telemetry and opt-in Issue reporting belong to [`diagnostics`](../diagnostics).

---

## 1. Domain Invariants (`device-tool`)

1. **Zero Accidental NPU Context & Standalone Operation (`DEV-ZERO-CTX`)**:
   - Top-level package imports and offline/pure-CPU paths (`inventory`, `analyze`, `correlate`, `compare`, `sql`, `camodel`, `kernels`, `inspect-op-abi`, `repro-op`, `sim_bridge`, `sim_native_bridge`, `sim_structure_ingress`, `bench abi --export-builders`, `bench diff`, `mindie_profiler/bench/env_fingerprint.py`, `mindie_profiler/bench/campaign_store.py`, `mindie_profiler/bench/l0_presets.py`) are pure CPU operations and must **never** import `torch_npu`, initialize CANN runtime contexts, or allocate HBM on `Phy-ID 0` (`0 MiB` HBM delta). `mindie-profiler` has **zero hard runtime dependency on `mindie-sim`** (`dependencies = ["ijson>=3.2,<4"]`, zero private `mindie_sim.*` imports across `mindie_profiler/**`); optional public-API hooks (`mindie_sim.public`, `mindie_sim.model_catalog`, `mindie_sim.structure`, `mindie_sim.cohort_accuracy`, `mindie_sim.simulate_native_call`) activate only when `mindie-sim` is separately installed.
   - Live device probing (`fabric_probe`, `thermal_guard`, `collect`, and live `bench` execution including bounded `npu-smi` live `Aicore curFreq` clock probing on `bench run-plan`/`sku`/`subgraph`) runs only when explicitly invoked by the caller (`--allow-cpu-smoke` disables `npu-smi` probing and marks observations `qualified=False`).
2. **In-Place Read-Only Analysis & Confined Staging (`DEV-READONLY-PATH`)**:
   - Offline analysis opens `ascend_pytorch_profiler_*.db` and `msprof_*.db` strictly read-only without mutating user profiling directories or polluting `cwd` / `$HOME`.
   - Trace sidecar indexes (`sources_trace.py`), CANN 9.x shim builds (`cann_abi.py`), and CAS reproducer slots (`repro_storage.py`, `repro_retention.py`) use atomic `os.replace` with symlink/NTFS-reparse-point rejection and bounded LRU/TTL eviction (`8` `.so` variants, `64` CAS/diff entries / `14d`). Incremental benchmark campaigns (`mindie_profiler/bench/campaign_store.py`) write strictly inside the caller-supplied `--campaign-dir` using write-once immutable per-run shards (`runs/<run_id>.jsonl`), `storage_locks.exclusive_lock`, atomic `os.replace` on `index.json` / `campaign_index.json`, `Never-Overwrite-Qualified`, and `portable_receipt()` scrubbing.
   - Auxiliary retention or sidecar cleanup warnings after primary artifact delivery keep primary success intact (`Receipt Honesty`), and every `except OSError:` boundary is preceded by `except TimeoutError: raise`.
3. **3-State Topology Alignment, Standalone Hardware/Observed Contracts & Fresh Upstream Parity (`DEV-TOPOLOGY`)**:
   - Declarative Ascend A2 / A3 dual-Die / A5 (`Ascend950DT_*` / `Ascend950PR_9579` / `Ascend950PR_958b`) hardware presets live in `mindie_profiler/knowledge/ascend_hardware_presets.json` (served by `hardware_presets.py`), and standalone observed operator/tensor/structure contracts live in `mindie_profiler/observed_contracts/` backed by `mindie_profiler/knowledge/observed_contract_specs.json` (with PEP 562 lazy forwarding shims on `body_*_contracts.py` / `tensor_contracts.py` / `structure_subgraphs.py` so `mindie-profiler` operates 100% standalone without `mindie-sim` installed).
   - Structural mapping (`structure_mapping.py`, `structure_subgraphs.py`) preserves 3-state attribution (`matched`, `unmatched_observed`, `unobserved_declared`) on `mindie-model-structure/1` and A2 / A3 dual-Die / A5 (`Ascend950DT_*` / `Ascend950PR_9579` / `Ascend950PR_958b`) topology without fabricating silent 1:1 matches or `0.0` fallback latencies (`declared_only` / `unavailable` when cohorts or peaks are incomplete).
   - Incremental silicon campaigns (`mindie_profiler/bench/env_fingerprint.py`, `mindie_profiler/bench/campaign_store.py`, `mindie_profiler/bench/campaign_runner.py`, `mindie_profiler/bench/timing.py`, `mindie_profiler/bench/subgraph_runtime.py`) partition buckets by 15 static stack-identity keys (`mindie-bench-env/1`) and 31-field `CanonicalKernelKey` digests, map dual-die A3 `Chip Phy-ID` to `(NPU ID, Chip ID)` via `npu-smi info -m` with single-chip section slicing (failing closed on ambiguous multi-chip output), require verified live clocks (`is_live_clock_source` + `validate_clock_band`), label `clock_operator="busy_union"` only from verified per-repeat traced kernel intervals (otherwise `"elapsed_span"`), isolate `FULL_DECODE_ONLY` `NPUGraph` capture/replay with `allclose` deterministic output verification, reject loopback execution for `inter_node` collectives, and enforce `training_manifest_sha256` heldout-vs-training geometry independence. The 106 canonical operator builders (`CANONICAL_BUILDERS`, `BuilderSpec` SSOT across `mindie_profiler/bench/operators*.py`) bind 1:1 to CANN 9.3.0 / HCCL / MC2 / Triton / `fla` kernels with zero `inspect.signature`, zero composite PyTorch fallbacks, zero RNG inside timed closures, and declarative bounds in `mindie_profiler/bench/bench_profiles.json`.
   - Verify fresh upstream `HEAD`s across the full Ascend stack (`vllm-ascend`, `cann-recipes-infer`, `MindIE-SD`, `cann/ops-transformer`, `cann/ops-nn`, `cann/catlass`, `fla-npu`, `flash-attn-npu`, `AscendC` / `Triton-Ascend`, `xllm` / `xllm-ops`, `torch-npu`) before updating operator normalization, `op_api_catalog.json`, or Advisor rules; cross-rank straggler and collective readiness accounting preserves explicit clock-alignment provenance (and CSV `--auto-step` requires real `Step Start Time(us)`).
4. **Bounded Memory, Clean-Core `mindie-sim` Bridge & Module Hygiene (`DEV-BOUNDED-MEM`)**:
   - Stream large JSON traces via `ijson`, scope multi-window PMU cache priming strictly to merged disjoint windows, and query SQLite slices in place (`<= 512 MiB` peak RSS; never whole-read traces `> 50 MiB`).
   - Bridge to `mindie-sim` strictly through public Clean-Core APIs (`sim_bridge.py`, `sim_bridge_catalog.py`, `sim_bridge_observed.py`, and consolidated `sim_native_bridge.py`) with zero deleted `sim_bridge_{case,cells,native_obs,predict}` / `opflow` / sidecar imports, emitting `mindie-bench-observation/2` for `mindie_sim.observations.bench_packets`.
   - Follow cohesion-first module governance: `~1,800` lines per module is a soft guideline (cohesive modules `> 1,800` lines such as `mindie_profiler/bench/campaign_runner.py` are permitted when declaring a top-30-line `[Role]` / `[Invariants]` / `[Timeouts & Locks]` / `[Side-Effect Policy]` docstring header, keeping functions `<= 150` non-table lines or `[Cohesive-Pipeline]` with control-flow nesting depth `<= 6`, and avoiding artificial `*_helpers`/`*_mixin`/`*_part<N>` shards), pass `scripts/check_no_magic_numbers.py`, and use Unix `LF` (`\n`) line endings.

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

# 2. Run the standalone non-live-NPU test suite (zero mindie-sim required)
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. Validate PR body against the device-tool design-principles checklist
python3 .github/scripts/check_pr_checklist.py --profile device-tool --body-file <pr_body.md>
```

---

## 4. Living Specifications

- Architecture & profiler contract: [`../mindie-agent/docs/profiler-system.md`](../mindie-agent/docs/profiler-system.md)
- Workspace routing & guardrails: [`../mindie-agent/AGENTS.md`](../mindie-agent/AGENTS.md) and [`../mindie-agent/docs/historical-issues-and-guardrails.md`](../mindie-agent/docs/historical-issues-and-guardrails.md)
