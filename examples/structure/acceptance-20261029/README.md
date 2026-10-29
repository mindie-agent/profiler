# Existing-capture acceptance, 2026-10-29

This acceptance reprocesses existing hardware captures in place. It does not
start an NPU workload or claim new live collection. Model declarations remain
independent of measured event order and duration. Saved replay JSON files retain
source identity, selected windows and `structure_mapping`; unrelated C7
enrichment is omitted to keep the evidence compact.

The latest [complete family/cohort replay](cohort-full-family-replay.md)
removes the comparison allowlist, adds the high-frequency matrix/norm/router
contracts, and reports all native families with explicit scored subsets and
remaining gaps. It includes current source identities and maintained tests.
Earlier sections below retain the outcomes of their original declarations.

The subsequent [attention/cache/fused body replay](body-contract-replay.md)
adds eight complete A3/A5 capture windows, source coverage inventory, explicit
comparison scopes and current per-model results. The counts in the original
sections below describe the earlier acceptance and its graph declarations.

## Complete A2 module replay

The original capture is a synchronized `Linear(256,512) -> ReLU ->
Linear(512,256)` workload, input `[8,256]`, FP32, on Ascend 910B4. Its DB is
38,690,816 bytes and its original module trace is 33,509,581 bytes. The DB SHA256
is `5ca5235f1e3e91c58909ffbc11b9041d963f0a210dbe87fcce787ac36523a72b`.
The [fixture provenance](../../../tests/fixtures/structure_module/provenance.json)
records original DB, trace, steps and result hashes; the full replay uses those
original files, not the six-event regression fixture.

The declaration is built by sim's existing `gemm_op`, `vector_op` and
`export_op_structure`. Exact module IDs `0`, `1`, `2` name the actual Sequential
modules. They are not Transformer layer numbers. The profiler streams the raw
24,000 invocation records, retains 18,000 inside the three selected steps and
recomputes attribution; it does not reuse the trace's old mapping summary.

[module-replay.json](module-replay.json) records:

| Selected scope | Device events | Bound events | Bound busy union coverage |
| --- | ---: | ---: | ---: |
| Step 1 | 6,000 | 6,000 | 100% |
| Step 2 | 6,000 | 6,000 | 100% |
| Step 3 | 6,000 | 6,000 | 100% |
| All selected steps | 18,000 | 18,000 | 100% in each independent window |

Each step has 2,000 events at each of the three declared nodes. The evidence
basis is `synchronized_module_and_tensor`, not manual event binding. Raw bias
tensors distinguish the two `matrix_bias` contracts from unbiased matmul.
The same six real regression events without module evidence remain candidates.

The final replay with compact output took 3.96 seconds with 198,230,016 bytes
peak RSS (about 189 MiB), below the 512 MiB routine-analysis budget. An earlier
full C7 output run took 6.83 seconds with about 220 MiB peak RSS.
This is local analysis cost, not device
performance. The original collector synchronizes at module boundaries, so these
measurements do not establish uninstrumented application throughput or full LLM
layer attribution.

From the profiler checkout, with the rewritten sim source on `PYTHONPATH`:

```bash
capture_root=/Volumes/data/temp/mindie-003-execution/execution-lane/wave4/profiler-live/baseline-v3-result/result
PYTHONPATH=.:../sim-rewrite-20261027 python examples/structure/replay_module_capture.py \
  --db "$capture_root/profile/b2bb20466bf7_49402_20261019214842958_ascend_pt/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler.db" \
  --module-trace "$capture_root/module_trace.json" \
  --steps "$capture_root/steps.json" \
  --output /tmp/module-replay.json
```

## Real Qwen Host connections

The four complete Qwen3-8B DBs preserve PyTorch/CANN connection evidence, but
their Host names contain no model-layer instance markers; all `callchainId`
values are zero. They prove Host-to-operator relationships, not model layers.

The adapter previously dereferenced both tables through `CONNECTION_IDS`.
Actual schema uses direct `CANN_API.connectionId -> TASK.connectionId`, while
`PYTORCH_API.connectionId -> CONNECTION_IDS.id -> connectionId` is an index.
The s1 DB contains 2,785 numeric namespace collisions.

In the same 5.6 ms window, the fix changes direct CANN connections from 0 to 9
and uniquely supported Host chains from 2 to 10, over ten positive-duration
tasks. The remaining task has a direct PyTorch connection but its CANN call is
outside that window. The old `matched_task_count=10` was insufficient: eight
matches relied on interval fallback. [host-correlation.json](host-correlation.json)
preserves before/after counts, concrete corrected chains, independent SQL,
source hash and reproduction command.

The full DB replay includes all three tables' time bounds, including launches
before the first device task. All **1,551 positive-duration TASK occurrences**
then have a unique connected Host chain: 1,551 direct CANN connections, 1,494
PyTorch connections and 57 unique same-thread containment chains. Independent
SQL agrees. There are no interval-only associations, duplicate global task IDs,
ambiguous connections or missing Host chains. A device-only time range omits two
earlier launches and produces 1,549/1,551 instead; both boundary checks are
retained in the evidence. The full replay took 9.986103 seconds.

## The 22 unmapped and 14 ambiguous A5 events

[fixture-mapping-reasons.json](fixture-mapping-reasons.json) audits every sample
against the complete original CSV, including source line, raw descriptors,
contract and declared candidates. No tensor field was lost by parsing.

| Original classification | Count | Result after this change |
| --- | ---: | --- |
| Different execution geometry, precision or declared scope | 20 | Explicit declaration-mismatch diagnostics |
| Unsupported 3D Slice | 1 | Native 3D contract parsed; still differs from the declared 2D view |
| Original tensor fields are N/A | 1 | Explicit missing-metadata diagnostic |
| Repeated contracts without module occurrence evidence | 14 | Remain ambiguous |
| Unique contracts without module occurrence evidence | 2 | Remain candidates |

The original request is 16,384 input tokens and 32 output tokens, concurrency 1,
with eager MTP3 and `FULL_DECODE_ONLY`. The 38 rows mix prefill, later generation
and additional precision/projection branches. Twenty of the 22 unmapped events
were compared against an incompatible single `prefill/tokens=16384/scope=model`
declaration. Tensor geometry alone does not prove which draft/verify branch ran.

The Slice has `[16384,128,128] -> [16384,48,128]`; the declaration has
`[16384,16384] -> [16384,6144]`. Equal per-row element counts do not prove the
same view or missing offset values. Consequently the honest after-state in
[a5-fixture-after.json](a5-fixture-after.json) remains **22 unmapped, 14 ambiguous,
2 candidates, 0 bound**, with actionable reasons.

The 14 ambiguous rows match repeated layer contracts. Two Slice rows additionally
match beta and alpha copies within a layer; recorded index tensor shapes do not
include their offset values. The retained A5 capture directory has no DB,
trace-view JSON or module trace. Its aggregated `operator_details.csv` has empty
Input Shapes/Call Stack and no occurrence timestamp or correlation/module ID.
`with_modules=true` in configuration is not evidence of a retained module trace.
The single `step_trace_time.csv` row has no step ID.

## Complete A5 capture and remaining support

[a5-full-prefill-declaration.json](a5-full-prefill-declaration.json) analyzes all
22,486 positive-duration events from the 7,978,835-byte original CSV, without
pretending the whole capture is one prefill:

- 1,116 ambiguous and 47 candidate events match declared tensor contracts.
- 11,774 events have incompatible declared geometry, descriptors or operator scope.
- 2,288 events lack captured tensor metadata.
- 7,261 events have operator types without an implemented observed contract.
- No event is bound to a layer without occurrence evidence.

The new 3D Slice and actual `SwiGlu` spelling produce contracts for 576 and 804
events respectively. Total unavailable contracts fall from 10,929 to 9,549;
this improvement is parser/contract coverage, not verified layer coverage.

[a5-contract-gap-triage.json](a5-contract-gap-triage.json) lists all 41 remaining
unsupported types, exact counts and representative original rows. Its type-level
engineering triage identifies 698 events of types with recognizable body
semantics, 3,375 shared primitives, 34 explicit runtime/sampling helpers and
3,154 generic helpers with unresolved ownership. These are not event-level
attributions: for example, `Add` cannot be labeled runtime merely from its name.
Remaining attention/cache/fused contracts and helper ownership are visible
limitations, not completed capabilities.

To reproduce the A5 declaration, use `examples/cases/qwen38-a5.json` from the
rewritten sim checkout with `export_structure(..., phase="prefill", tokens=16384,
scope="model")`, then analyze the original CSV using `full_range=True`.
The source and its content hash are retained in both the audit and replay
projection. Do not supply `scene.phase="prefill"` for the mixed-phase capture.

## Regression evidence

`tests/test_structure_module_acceptance.py` uses unchanged real A2 events and
raw module records for the positive path. Controlled mutations verify that
cross-step overlaps, wrong step IDs, boundary-crossing events, source hash
mismatches and unsynchronized records cannot manufacture a binding. It also
checks that old mapping summaries are ignored and the record budget is enforced.

`tests/test_profiler_inventory_correlate.py` uses real Qwen schema/rows, including
API tables without synthetic `id` columns and a real namespace collision.
Missing connection rows or tables cannot fall back to literal PyTorch IDs.
Structure tests preserve nested scope constraints, geometry/precision diagnostics
and independent interval accounting. None of these tests claims a new live run.

Final local verification with both development checkouts available:

- Profiler maintained suite: **386 passed, 26 skipped**, 6.28 seconds.
- Rewritten sim maintained suite excluding `live_npu`: **967 passed**, 242.13 seconds.
- Changed source, example, fixture metadata and product documentation files use
  LF; `git diff --check` passed in all three affected repositories.
