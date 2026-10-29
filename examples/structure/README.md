# Declared model structure and measured attribution

This development workflow reuses sim's model catalog, layer plans and graph
builders. Profiler parses the original capture and attaches actual event
occurrences to that declaration. It does not maintain a second model registry,
import sim, or infer layer numbers from event order or duration.

## Install matching sources

The shared `normalized`, `tensor_contracts` and structure-mapping APIs are current
development code. Released `mindie-profiler 0.5.0` does not include these APIs;
sim's optional `mindie-profiler>=0.5.0` dependency alone does not establish their
compatibility. With adjacent profiler and rewritten sim checkouts, from sim:

```bash
python -m pip install -e .
python -m pip install -e ../profiler
```

Ordinary simulation and structure export work without profiler. Only explicit
profiling adapters import it lazily. This workflow does not claim a coordinated
formal release.

## Export and inspect

Use the same complete `case.json` accepted by sim. Its model, implementation,
parallel layout and workload must describe the graph being investigated. Machine
fields satisfy the existing Case schema; structure export does not calculate
rates, load weights or initialize a device.

```bash
python -m mindie_sim.structure case.json \
  --phase prefill --tokens 16384 --scope body --output structure.json
mindie-profiler inventory --root /path/to/capture --output inventory.json
mindie-profiler analyze --root /path/to/capture --full-range \
  --structure structure.json --output mapped.json
```

Select explicit windows for a large or mixed-phase capture. Export accepts
`phase=prefill|decode` and `scope=body|model`, covering the first independent DP
cohort. `mindie-model-structure/1` preserves replica, stage, layer, block, family,
tensor contract, dependencies, implementation boundary and lineage. Its
`graph_id` hashes the declaration excluding caller source provenance and contains
no measured or predicted duration.

The optional `subgraphs` array describes native implementation boundaries over
existing semantic nodes. Its members, dependencies and external outputs come
from the same sim graph and recipe expansion. These are matchable composite
boundaries, not additional work. `structural_classification` reports properties
shared by all compatible candidates; `windows.structural_groups` aggregates
their measured intervals without claiming an individual layer.

An explicitly supplied analysis `--phase` must agree with the exported execution
phase. If omitted, profiler does not infer it from the trace. The report retains
the declaration and caller-supplied phase separately, along with bound nodes'
contract scopes.

Read `structure_mapping` in the returned C7 report before interpreting layer
costs. A unique tensor match is `candidate`; repeated layers remain `ambiguous`.
Missing fields and unmatched work remain `unmapped`. No event association means
that a declared node is unobserved, not that its actual cost is zero.

## Add event evidence

`--bindings bindings.json` accepts `mindie-profile-bindings/1` with the exported
`graph_id`. Copy concrete `event_id` values from the report, node IDs from the
manifest, and state the actual source of the association:

```json
{
  "schema_version": "mindie-profile-bindings/1",
  "graph_id": "<graph_id from structure.json>",
  "rank_replicas": {"rank_0": 0},
  "rank_stages": {"rank_0": 0},
  "events": [
    {
      "event_id": "<specific event_id from mapped.json>",
      "node_ids": ["<declared node_id>"],
      "relation": "direct",
      "evidence": {"source": "<reviewed annotation or source of the association>"}
    }
  ]
}
```

The placeholders are illustrative. Binding an event explicitly reports
`basis=explicit_evidence`; it does not turn a caller assertion into automatic
model recognition. Event IDs include source locators and occurrence intervals,
not a capture-content hash. Reused `globalTaskId` values are insufficient.

For supported Host evidence, add exact `host_scopes` frame names and their
`node_ids` in the binding file and pass one or more `--correlation FILE` outputs
from `mindie-profiler correlate`. Binding requires an actual Host connection to
the concrete task occurrence and a unique tensor match within that scope.
Correlation also checks source path, size and modification time.

The task's `globalTaskId` must occur exactly once in the complete TASK table.
Direct Task-to-Host connections must be unique. A CANN path requires a unique
Task-to-CANN connection and either a unique Host connection or an unambiguous
strict same-thread Host ancestry chain. Equal or crossing Host intervals,
multiple connection candidates and device interval containment alone cannot
establish an automatic binding. If multiple correlation reports supply scopes
for one occurrence, every scope must support the same unique tensor candidate;
conflicting scopes remain ambiguous.

`CANN_API.connectionId` directly names a TASK connection. In the supported
PyTorch DB schema, `PYTORCH_API.connectionId` instead indexes `CONNECTION_IDS.id`.
These numeric namespaces can overlap; profiler resolves each according to its
table. A missing PyTorch index mapping is missing evidence, not a direct ID.

For an existing `mindie-module-trace/1`, use repeatable `--module-trace FILE`
and declare exact `module_scopes` in the same bindings file:

```json
{
  "schema_version": "mindie-profile-bindings/1",
  "graph_id": "<graph_id>",
  "module_scopes": [
    {"module_id": "0", "node_ids": ["rank:0/0"]},
    {"module_id": "1", "node_ids": ["rank:0/1"]},
    {"module_id": "2", "node_ids": ["rank:0/2"]}
  ]
}
```

The trace must carry `source_identity.db_sha256` and synchronized NPU boundaries.
Profiler verifies the selected DB content, streams raw invocation records and
ignores previous mapping summaries. Only unique full event containment, a
consistent step and one matching tensor contract within the declared module
scope can bind. Overlapping invocations, including cross-step overlaps, remain
ambiguous. Nested Host scopes all participate in the intersection; contradictory
ancestors cannot be discarded. The retained module records share one total
`--max-mapping-events` budget across input traces.

For a workload outside the transformer catalog, sim's
`export_op_structure(ops, *, model, execution, kernels=None, source=None,
expand_calls=True)` accepts existing declared `OpSpec` graphs and uses the same
manifest exporter. The [tiny-MLP replay example](replay_module_capture.py) declares
Linear/ReLU/Linear from the workload source using sim's existing operators.
It preserves Linear bias and uses `layer=-1` for modules outside a transformer.
There is no profiler-local model catalog or weight loading.

Rank-to-replica and rank-to-stage assignments are caller declarations. Unspecified
assignments retain candidates; physical rank numbers are not assumed to be DP
replicas. Multiple events can bind one node. A fused event uses
`relation="fusion"` and multiple node IDs within one replica and stage. Nodes
retain inclusive shared time; layer, block and window totals use interval unions
without double counting. Node totals therefore cannot be added together.

For a declared composite, use one `subgraph_ids` entry instead of `node_ids`:

```json
{
  "event_id": "<specific event_id>",
  "subgraph_ids": ["<subgraph_id from the manifest>"],
  "evidence": {"source": "<independent occurrence evidence>"}
}
```

An explicit subgraph binding must agree with the observed tensor contract.
Host/module scopes also accept `subgraph_ids`; a scope described by `node_ids`
must contain every member to include a fusion. All enclosing evidence scopes
still intersect. Binding only one child cannot identify its enclosing fusion.
Measured composite time is reported once in `windows.subgraphs`, with
`member_timing=not_separately_measured`; it is not distributed among the
semantic children. `covered_node_ids` retains the association separately from
individual node timing.

The default `--mapping-limit 200` caps displayed event mappings, not accounting.
`--max-mapping-events 100000` caps processed event-window occurrences and raises a
visible error when exceeded. Each event reports the full `candidate_count` and
up to 64 node candidates and 64 subgraph candidates. `candidate_count` counts
matching boundaries, not their semantic members.

`reason_counts`, `diagnostic_counts` and each retained row's `diagnostic` separate
absent captured tensor fields, unsupported contracts, incompatible declarations,
missing occurrence evidence and conflicting supplied evidence. Near contracts
only explain declaration differences; they never become verified candidates.
Three-dimensional Slice retains its original rank, and missing slice offsets
remain missing. An equal element count after flattening is not an exact match.

## Comparison and verification boundary

Sim operator comparisons reuse profiler's normalized raw observations and tensor
contracts. `windows[].cohorts` additionally reconciles repeated candidates with
equal tensor contracts, physical work and placement. It reports measured call
count versus declared instances and Transformer blocks, complete-event Mean/P50,
activity sum and interval union. Host/module conflicts, overlapping boundaries
and different physical work remain explicitly excluded. No counts are converted
to layer identities or inferred step counts.
For a single captured device, complete symmetric DP alternatives can form one
cohort while `replica` stays unknown. All candidate IDs remain available;
`declared_candidate_instance_count` records their total and
`declared_instance_count` records the count per device. The sim consumer verifies
identical physical hardware before pricing a representative. A trusted specific
occurrence binding retains its known replica.

The sim consumer accepts either the `analyze` C7 report or its
`mindie-profile-structure-mapping/1` object:

```bash
python -m mindie_sim.cohort_comparison case.json mapped.json -o comparison.json
```

The case must regenerate the same graph identity. Selected native fusion
resources use one device program and remove only source-proven internal HBM
materializations. The exporter retains semantic members, the physical
`resource_boundary`, and work/signature fields; fused internal nodes cannot
independently match events. Unselected multi-program subgraphs remain
`reference_only` without a fused-kernel error score. Single-program cohorts can
compare per-call predictions with measured Mean/P50 and cumulative activity,
conditional on their explicit contract scope. Clipped events do not receive an
error score. Attribution does not automatically calibrate primitives or assign
training versus heldout roles.

The complete-capture runner has no native-type allowlist: every cohort with a
valid contract and physical work enters `compare_cohorts`. Each distinct
physical program has its own process budget; a failure keeps the measured
statistics and a visible failure reason. The family tables include all observed
native types, with full event/activity denominators, scored/reference counts and excluded
reasons. Residuals describe only the scored subset. A declared W4A8 matrix
without its correction/rescale epilogue remains `reference_only`, even though
its matrix geometry forms a valid cohort. MXFP4 programs with an unmodeled
native unpack/scale/matrix path also remain references. The replay entry point is
`replay_fusion_cohorts.py --run`; `--compare-existing --run` reuses saved mappings
and still verifies their graph identity.

Accuracy is evaluated per cohort using the observed complete-event mean:
above 50 us, absolute relative error must be at most 15%; at or below 50 us,
the absolute per-call difference must be at most 15 us. The latter reports
`within_launch_floor_tolerance`. This acceptance allowance does not add a floor
to predictions or attribute the residual to measured launch overhead.
The shared sim policy exports `observed_per_call_us`, `predicted_per_call_us`,
`per_call_diff_us` (predicted minus observed), `abs_error_per_call_us`,
`accuracy_tier`, `accuracy_status`, `accuracy_pass`, `accuracy_tolerance` and
versioned `accuracy_policy`. References and unscored rows have no pass decision.

Family means are weighted by scored call counts. Acceptance and counts are
aggregated from individual cohorts, separately by tier, so a family mean cannot
hide a slower failed cohort. Event-weighted pass counts describe cohort-mean
decisions, not a test of each event. Top Errors separates large-call failures,
small-call failures, within-tolerance groups and unscored coverage; original
relative and cumulative residuals remain available.

```bash
PYTHONPATH=/path/to/sim-rewrite:/path/to/profiler /path/to/sim-rewrite/.venv/bin/python \
  examples/structure/replay_fusion_cohorts.py --refresh-accuracy --run
```

This mode checks saved artifact identities and refreshes all completed variants.
It reads neither raw captures nor weights and does not execute predictions.
Original observed/predicted values, graph IDs and residuals remain identical;
`fusion-cohort-accuracy-validation.json` records the policy refresh separately
from the historical full-replay receipt.

Kimi's current-checkpoint variants retain independently collected per-module
quantization metadata. Their config hash matches the historical campaign, but
the historical quantization-file hash was not retained. They are conditional
declarations, separate from the original catalog case and from captured-dispatch
proof. Kimi phase/configuration variants are scanned serially to bound memory.
The selected GLM variants reuse the independently declared MSD source case,
including integer balanced routing, nominal INT4 supply and the chosen matrix
program. Norm-bias and MLA/indexer declarations remain explicit. These cases
do not establish the capture's expert histogram, kernel dispatch or cache
residency. Generic single-launch fusion inherits incomplete member costs;
only a source program that implements the missing work removes that restriction.

The retained `mindie-modeling-inputs/1` and legacy `pipeline --durations` exports
are separate interfaces, not native inputs of rewritten sim.

## Decode body and layer comparisons

`replay_decode_forwards.py` is an optional Sim consumer. A source-pinned manifest
names the original capture, Sim case and an existing `extraction_path`; the
driver reuses complete Forward populations without rescanning the capture.
Automatic structure-guided alignment reports conditional layer ordinals, not
Host/module occurrence bindings. Every observed query/batch geometry keeps its
own denominator. `--geometry-limit 1` predicts the largest population per source
first and retains the other buckets with a visible deferred reason and no score.

```bash
PYTHONPATH=/path/to/sim-rewrite:/path/to/profiler /path/to/sim-rewrite/.venv/bin/python \
  examples/structure/replay_decode_forwards.py --manifest cases.json \
  --prediction-cache-dir /tmp/mindie-body-predictions --prediction-timeout 240 \
  --geometry-limit 1 --output body-report.json
```

Body and layer spans use first kernel invocation through final completion;
internal gaps and real collective waits remain in the span. Layer 0 and full
body statistics remain separate from explicitly labelled steady-layer samples.
The compact `scheduled_operator_summary` groups predicted intervals by replica,
pipeline stage, family, recipe and program and retains the longest ten nodes per
replica. Those intervals include resource/peer waits and may overlap: their sum
is not hardware service time or an additive decomposition of body latency.

Reports retain the selected runtime hash, case identity and adapter identity.
Different checkpoint, SP or runtime declarations are separate comparison arms
over the same source population; they do not create additional measured samples.
Client concurrency is distinct from exported execution slots, and a single
captured rank does not prove symmetric activity across DP peers.

From the profiler checkout, with the matching sim source directory on the import
path, run the cross-component offline acceptance:

```bash
PYTHONPATH=.:../sim python -m pytest -q tests/test_structure_sim_acceptance.py
```

Adjust `../sim` to the rewritten sim checkout. Missing sim source or its capture
fixture is an explicit skip. Tests verify an unchanged provenance-backed A5 CSV
slice through real graph export and parsing, repeated-layer ambiguity, controlled
direct/fusion associations, duration-only perturbation and output limits. The
GLM45 DB slice supplies 26 real occurrences of one replay task ID; explicit
bindings select two without binding the other occurrences or filling missing
tensor fields. These are offline capture replays and algorithm controls, not new
NPU runs or evidence that the controlled model declaration ran on hardware.

The [2026-10-29 acceptance record](acceptance-20261029/README.md) adds a fresh
replay of the complete historical A2 module capture: all 18,000 device events
bind to the three independently declared modules. It also documents the real
Qwen Host-connection fix and why the 38-row A5 sample's 22 unmapped and 14
ambiguous events cannot honestly be forced into layers. The complete mixed-phase
A5 CSV is analyzed separately, including remaining unsupported operator types.
