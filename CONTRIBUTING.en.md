# Contributing to `mindie-profiler`

[简体中文](CONTRIBUTING.md)

`mindie-profiler` (`mindie_profiler`, `requires-python >= 3.11`) owns controlled Ascend NPU profiling capture, in-place read-only `msprof` SQLite/CSV/trace analysis, `P0–P4` HBM memory attribution, operator C-ABI inspection & sanitized single-op reproducers (`inspect-op-abi` / `repro-op`), 3-state `mindie-model-structure/1` topology alignment, and read-only C7 measured-supply bridging to `mindie-sim`.

## 1. Flat Sibling & Linked-Worktree Workflow

Keep primary checkouts on clean `main` and develop inside an isolated linked worktree under `../.worktrees/`:

```bash
git -C ../profiler fetch origin
git -C ../profiler worktree add -b feat/<topic> ../.worktrees/profiler-<topic> origin/main
cd ../.worktrees/profiler-<topic>
```

## 2. `mindie-sim` SSOT Boundary & Fresh Upstream Truth

1. **Single Source of Truth (`mindie-sim` Delegation)**:
   - Never duplicate model catalog geometry, Ascend SKU hardware peaks/topologies (`A2`, `A3` dual-Die, `A5` `Ascend950DT_*` / `Ascend950PR_9579` / `Ascend950PR_958b`), observed operator/communication contracts, or closed-form subgraph FLOP/byte math inside `mindie_profiler`. Delegate directly to `mindie_sim.model_catalog`, `mindie_sim.backends.ascend.profiles()`, `mindie_sim.observed_contracts`, and `mindie_sim.subgraph_math` through PEP 562 `__getattr__` lazy shims so `python -I` top-level imports remain lightweight and zero-device-context.
2. **Full-Stack Upstream Source Verification**:
   - Mount and verify the latest `HEAD` revision of the owning upstream repository across the Ascend stack (`vllm-ascend`, `cann-recipes-infer`, `MindIE-SD`, `cann/ops-transformer`, `cann/ops-nn`, `fla-npu`, `flash-attn-npu`, `cannbot-dsl`, `xllm` / `xllm-ops`, `torch-npu`) plus real captures before updating operator normalization, `op_api_catalog.json`, or Advisor rules (e.g., match fused `MoeGatingTopK` / `MoeInitRoutingV3` before generic `topk`/`scatter`, and require explicit `Step Start Time(us)` on CSV `--auto-step`).

## 3. Local Setup & Test Isolation

All tests isolate temporary directories and host environment variables automatically via [`tests/conftest.py`](tests/conftest.py) and [`tests/temp_workspaces.py`](tests/temp_workspaces.py):

```bash
# 1. Verify Unix LF line endings and zero new magic-number debt
python3 .github/scripts/check_lf_eol.py
python3 -B scripts/check_no_magic_numbers.py \
  --root profiler=mindie_profiler \
  --baseline scripts/magic_number_baseline.json \
  --exceptions scripts/magic_number_exceptions.json

# 2. Prebuild mindie-sim C accelerator & run Tier 0 + Tier 1 non-live-NPU tests
python3 -B -c "import mindie_sim.prediction.runtime.accel_build as b; b.build_accel()"
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. Run Tier 2 non-destructive live NPU verification when connected to standing A2/A3/A5 hosts
pytest -q -m live_npu
```

## 4. Installed-Wheel Smoke Verification

Verify the built wheel outside the repository checkout so packaged JSON/C assets (`knowledge/*.json`, `_cann9_capture_shim.c`, `_cann9_capture_mspti.h`) and entrypoints are checked without `PYTHONPATH=.`:

```bash
uv build
tmpdir="$(mktemp -d)"
uv venv "$tmpdir/venv"
uv pip install --python "$tmpdir/venv/bin/python" --no-deps dist/*.whl
(cd "$tmpdir" && "$tmpdir/venv/bin/mindie-profiler" --help)
rm -rf "$tmpdir"
```

## 5. Pull Request Checklist (`device-tool` Profile)

Every PR must complete [`.github/pull_request_template.md`](.github/pull_request_template.md) and pass `python3 .github/scripts/check_pr_checklist.py --profile device-tool`:

- `DEV-ZERO-CTX`: Offline analysis, C-ABI inspection, and PEP 562 lazy `mindie-sim` bridge paths never import `torch_npu` or allocate HBM on `Phy-ID 0`.
- `DEV-READONLY-PATH`: In-place read-only SQLite/trace analysis (`immutable=1` fallback restricted strictly to sealed sidecar-free `CANTOPEN`, never `SQLITE_BUSY`), symlink/reparse-safe atomic `os.replace` on CAS/shim/sidecar caches, Receipt Honesty, and `TimeoutError` propagation before `OSError`.
- `DEV-TOPOLOGY`: Zero local duplication of model catalog, SKU peaks, observed contracts, or subgraph math (`mindie-sim` SSOT); exact 3-state `mindie-model-structure/1` attribution, cross-rank clock alignment, A2/A3 dual-Die/A5 (`DT` + `PR_9579/958b`) semantics, and fresh owning upstream repo (`vllm-ascend` / `cann-recipes-infer` / `MindIE-SD` / `ops-transformer` / `ops-nn` / `fla-npu` / `flash-attn-npu` / `cannbot-dsl`, etc.) operator classification.
- `DEV-BOUNDED-MEM`: Streaming `ijson` / SQLite I/O and disjoint-window PMU cache priming (`<= 512 MiB` peak RSS), `< 800`-line modules with 4-part headers, `check_no_magic_numbers.py`, and Unix `LF` line endings.
