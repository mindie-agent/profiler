## 变更摘要 (Summary)

- Describe the root cause / profiling contract and the resulting behavioral change.

## 设计原则 Review (Pre-PR Checklist — `device-tool`)

- [ ] **DEV-ZERO-CTX** — Offline analysis, C-ABI inspection, and PEP 562 lazy `mindie-sim` bridge paths never dynamically import `torch_npu` or initialize NPU contexts (`0 MiB` HBM delta; clean `python -I` top-level import).
- [ ] **DEV-READONLY-PATH** — User profiling artifacts are analyzed strictly read-only (`immutable=1` restricted to sealed sidecar-free `CANTOPEN`, never `SQLITE_BUSY`); sidecar/CAS/shim caches enforce symlink/reparse guards + atomic `os.replace`, stop/recovery precedes receipt persistence, and `TimeoutError` re-raises before `OSError`.
- [ ] **DEV-TOPOLOGY** — Zero local duplication of model catalog, SKU peaks, observed contracts, or subgraph math (`mindie-sim` SSOT); 3-state `mindie-model-structure/1` attribution, cross-rank clock alignment, A2/A3 dual-Die/A5 (`DT` + `PR_9579/958b`) semantics, and fresh owning upstream repo (`vllm-ascend` / `cann-recipes-infer` / `MindIE-SD` / `ops-transformer` / `ops-nn` / `cann/catlass` / `fla-npu` / `flash-attn-npu` / `AscendC` / `Triton-Ascend`, etc.) operator classification hold without silent fallbacks.
- [ ] **DEV-BOUNDED-MEM** — Large traces stream via `ijson` / SQLite slices with disjoint-window PMU cache priming (`<= 512 MiB` RAM), core modules stay `< 800` lines with top-30-line 4-section headers, `check_no_magic_numbers.py` passes, and all files use Unix `LF`.

## 证据记录 (Evidence)

- **DEV-ZERO-CTX**: `<command / python -I import & 0-ctx test output, or not-applicable: docs-only>`
- **DEV-READONLY-PATH**: `<command / test and observed filesystem state, or not-applicable: docs-only>`
- **DEV-TOPOLOGY**: `<mindie-sim SSOT check, upstream repo@revision verified, fixture or live result, or not-applicable: docs-only>`
- **DEV-BOUNDED-MEM**: `<check_no_magic_numbers.py, memory/module bound & LF check output, or not-applicable: docs-only>`

## 验证结果 (Verification)

- Executed test suites (`pytest`, `check_no_magic_numbers.py`), wheel smoke test, LF check, and any unexecuted live-hardware scope.
