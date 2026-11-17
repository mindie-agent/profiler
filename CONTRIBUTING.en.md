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

## 2. Local Setup & Test Isolation

All tests isolate temporary directories and host environment variables automatically via [`tests/conftest.py`](tests/conftest.py) and [`tests/temp_workspaces.py`](tests/temp_workspaces.py):

```bash
# 1. Verify Unix LF line endings
python3 .github/scripts/check_lf_eol.py

# 2. Prebuild mindie-sim C accelerator & run Tier 0 + Tier 1 non-live-NPU tests
python3 -B -c "import mindie_sim.prediction.runtime.accel_build as b; b.build_accel()"
pytest -q -n auto --dist worksteal -p no:cacheprovider -m "not live_npu"

# 3. Run Tier 2 non-destructive live NPU verification when connected to standing A2/A3 hosts
pytest -q -m live_npu
```

## 3. Installed-Wheel Smoke Verification

Verify the built wheel outside the repository checkout so packaged JSON/C assets (`knowledge/*.json`, `_cann9_capture_shim.c`, `_cann9_capture_mspti.h`) and entrypoints are checked without `PYTHONPATH=.`:

```bash
uv build
tmpdir="$(mktemp -d)"
uv venv "$tmpdir/venv"
uv pip install --python "$tmpdir/venv/bin/python" --no-deps dist/*.whl
(cd "$tmpdir" && "$tmpdir/venv/bin/mindie-profiler" --help)
rm -rf "$tmpdir"
```

## 4. Pull Request Checklist (`device-tool` Profile)

Every PR must complete [`.github/pull_request_template.md`](.github/pull_request_template.md) and pass `python3 .github/scripts/check_pr_checklist.py --profile device-tool`:

- `DEV-ZERO-CTX`: Offline analysis, C-ABI inspection, and `sim` bridge paths never import `torch_npu` or allocate HBM on `Phy-ID 0`.
- `DEV-READONLY-PATH`: In-place read-only SQLite/trace analysis, symlink/reparse-safe atomic `os.replace` on CAS/shim/sidecar caches, Receipt Honesty on retention warnings, and `TimeoutError` propagation before `OSError`.
- `DEV-TOPOLOGY`: Exact 3-state `mindie-model-structure/1` attribution, cross-rank clock alignment, and A2/A3 dual-Die/A5 topology semantics.
- `DEV-BOUNDED-MEM`: Streaming `ijson` / SQLite I/O (`<= 512 MiB` peak RSS), `< 800`-line modules with 4-part headers, and Unix `LF` line endings.
