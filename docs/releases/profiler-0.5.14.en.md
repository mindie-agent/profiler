# mindie-profiler 0.5.14

[中文](profiler-0.5.14.md)

This release pairs with formally published [`mindie-sim 0.9.14`](https://github.com/mindie-agent/sim/releases/tag/v0.9.14). Preserving all `0.5.12` capabilities — CANN 9.x steady-state MSPTI/`aclprof` capture, C7 collective-readiness extraction, native-call (`BIND1`) relational attribution, and active-pipe PMU measured supply — it adds operator C-ABI catalog inspection (`inspect-op`), content-addressed single-operator reproducers (`repro-op`), cluster interconnect probe emission and validation (`fabric-probe`), theoretical physical floor and two-tier Roofline annotation (`op-formula`), and `ACLGraph` multi-stream DAG and overlap diagnostics. Historical captures and fleet accuracy benchmarks are not relabeled as new measurements:

- **Ascend Operator C-ABI Catalog Lookup & Paginated Inspection (`mindie-profiler inspect-op`, `mindie_profiler/op_api_registry.py`, `mindie_profiler/op_api_paging.py`)**:
  - Ships a pinned CANN `aclnn` and custom fused-operator C-ABI slot catalog (`op_api_catalog.json`), supporting bounded queries by operator name, CANN release, and slot span for tensor inputs, scalar attributes, workspaces, and effective token-row semantics (`mindie-op-abi-inspect/1`) alongside MCP tool specifications.
- **Content-Addressed Single-Operator Reproducer Generation (`mindie-profiler repro-op`, `mindie_profiler/repro_*.py`, `mindie_profiler/op_abi_*.py`)**:
  - Binds captured operator occurrences (`--occurrence`) to exact ABI slot contracts and emits self-contained `sha256:<64-hex>` content-addressed `repro.py` NPU harnesses with deterministic tensor synthesis specs (`mindie-op-repro-receipt/1`), closing the loop with `mindie-sim diff-trace` offender commands.
- **Cluster Interconnect Microbenchmark Emitter & Receipt Validator (`mindie-profiler fabric-probe`, `mindie_profiler/fabric_probe*.py`)**:
  - Emits standalone multi-rank HCCL latency/bandwidth microbenchmark scripts (`--emit-script`) and validates measured probe outputs (`--parse-receipt`) into `mindie-fabric-probe/1` calibrated interconnect supply receipts ready for `mindie-sim` Mode B (`CalibratedFabricProfile`).
- **Per-Operator Theoretical Physical Floors & Two-Tier Roofline Annotation (`mindie-profiler op-formula`, `mindie_profiler/op_formula_*.py`)**:
  - Evaluates exact algebraic FLOPs, memory bytes, hard physical floors, and calibrated Roofline reference bounds (`mindie-op-formula-mcp/1`) for individual operators or batch kernel rows via `mindie_sim.op_formulas`, flagging sub-floor measurement or attribution anomalies first.
- **`ACLGraph` Capture/Replay Dependency DAG & Multi-Stream Overlap Diagnostics (`mindie_profiler/aclgraph_*.py`)**:
  - Reconstructs cross-stream event dependency DAGs across `ACLGraph` capture and replay (`reconstruct_aclgraph_dag`), classifies multi-stream serialization causes across five diagnostic regimes (`diagnose_aclgraph_overlap`), and evaluates Ascend SQ/CQ hardware queue budgets and SuperKernel device-loop fusion eligibility.
- **Hardened Structure Mapping Ingress & Centralized Configuration Governance (`mindie_profiler/structure_mapping.py`, `mindie_profiler/profiler_configs.py`)**:
  - Enforces bounded metadata snapshots on `StructureTargets` / `StructureMapper` while preserving `native-call-binding/1` verification and HCCL alias interval-union deduplication, and consolidates timeout, sampling, and threshold constants in `profiler_configs.py` with automated magic-number hygiene checks.
