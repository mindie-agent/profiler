## 变更摘要 (Summary)

- Describe the root cause / profiling contract and the resulting behavioral change.

## 设计原则 Review (Pre-PR Checklist — `device-tool`)

- [ ] **DEV-ZERO-CTX** — Offline analysis, C-ABI inspection, and `mindie-sim` bridge paths never dynamically import `torch_npu` or initialize NPU contexts (`0 MiB` HBM delta).
- [ ] **DEV-READONLY-PATH** — User profiling artifacts are analyzed strictly read-only; sidecar/CAS/shim caches enforce symlink/reparse guards + atomic `os.replace`, preserve primary delivery on retention warnings, and re-raise `TimeoutError` before `OSError`.
- [ ] **DEV-TOPOLOGY** — 3-state `mindie-model-structure/1` topology mapping, cross-rank clock alignment, and A2/A3 dual-Die/A5 interconnect semantics remain exact without silent fallbacks.
- [ ] **DEV-BOUNDED-MEM** — Large traces stream via `ijson` / SQLite slices (`<= 512 MiB` RAM), core modules stay `< 800` lines with top-30-line 4-section headers, and all files use Unix `LF`.

## 证据记录 (Evidence)

- **DEV-ZERO-CTX**: `<command / test and measured output, or not-applicable: docs-only>`
- **DEV-READONLY-PATH**: `<command / test and observed filesystem state, or not-applicable: docs-only>`
- **DEV-TOPOLOGY**: `<command / fixture or live A2/A3 result, or not-applicable: docs-only>`
- **DEV-BOUNDED-MEM**: `<command / memory & module bound check, or not-applicable: docs-only>`

## 验证结果 (Verification)

- Executed test suites, wheel smoke test, LF check, and any unexecuted live-hardware scope.
