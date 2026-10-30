# mindie-profiler 0.5.1: Streaming Native-Library SHA256 Digest, SQLite Busy-Timeout Alignment & Root CLI Contract

[中文](https://github.com/mindie-agent/profiler/blob/v0.5.1/docs/releases/profiler-0.5.1.md)

`mindie-profiler 0.5.1` switches native library SHA256 hashing to streaming `hashlib.file_digest` (eliminating whole-file `read_bytes()` memory spikes), enforces `>= 3000ms` SQLite `busy_timeout` across database readers/writers, prevents `except OSError:` blocks from swallowing `TimeoutError`, and clarifies root CLI `-h/--help` and unknown-subcommand diagnostics.

---

## 1. Key Features & Behavior Changes

### 1. Streaming Native-Library SHA256 Checks (`mindie_profiler/vllm_online_evidence.py`, PR `#5`)

- Online evidence collection now computes native shared-library (`.so`) SHA256 digests via streaming `hashlib.file_digest(fh, "sha256")` instead of loading entire binary files into memory with `Path.read_bytes()`, keeping control-plane working sets strictly bounded.

### 2. SQLite `busy_timeout >= 3s`, `TimeoutError` Propagation & Host Test Isolation (PR `#6`)

- **SQLite Lock Timeout Alignment**: Standardized SQLite connection setup in `memory_db.py`, `sources_db.py`, and `sql.py` with `timeout=5.0` and `PRAGMA busy_timeout=5000` (plus `PRAGMA journal_mode=WAL` on writable connections) to prevent transient lock contention failures during concurrent profiling analysis.
- **Explicit `TimeoutError` Propagation**: Because `TimeoutError` is a subclass of `OSError` in Python 3.11+, audited all `except OSError:` handlers across `analyze.py`, `collect.py`, `compare_acceptance.py`, `framework_capture.py`, `inventory.py`, `memory_evidence.py`, `memory_sampler.py`, `segment.py`, `sources_csv.py`, `sources_trace.py`, `tensor_cast_provider.py`, `theoretical_model.py`, `thermal_guard.py`, `vllm_online_evidence.py`, `vllm_online_memory.py`, and `weight_inspector.py` to re-raise `TimeoutError` before catching `OSError`.
- **Bounded Test Subprocesses & Host Isolation**: Added explicit `timeout=5` budgets to `git` subprocess calls in `tests/test_profiler_provider.py` and isolated host environment variables in `tests/conftest.py`.

### 3. Root CLI Help & Unknown-Subcommand Error Contract (`mindie_profiler/__main__.py`, PR `#6`)

- Added `_root_parser()` so `mindie-profiler -h` / `--help` prints root usage and lists all supported subcommands (`inventory`, `analyze`, `correlate`, `compare`, `sql`, `collect`) while documenting option-first `analyze` invocation.
- Invoking an unknown positional subcommand now immediately emits `mindie_profiler: unknown command ... (choose from ...)` to `stderr` and exits with code `2` instead of falling through to `analyze`.

---

## 2. Verification & Evidence Boundary

- **Automated Verification**: Full offline test suite (`pytest -q -m "not live_npu"`, including `tests/test_profiler_cli_root.py`) passes.
- **Evidence Boundary**: This release hardens streaming I/O memory bounds, SQLite concurrency timeouts, `TimeoutError` honesty, and CLI argument handling without altering the C7 `mindie-profile-summary/1` report schema.
