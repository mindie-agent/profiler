# Kimi AttnRes independent conditional reference

Status: **reference_only**. Sim source revision `2c0b339a250b811250d66b2ace109abcd6f8c548`. The separate 35-variant replay uses `6018eaa1c3ac3ef867cc1b7d696fc1642f2c2cf7`; this report does not add scored events to it.

This audit verified committed Git bytes and recomputed retained evidence arithmetic. It did not run the predictor, export a graph, or rescan the raw capture. Supplied execution reports remain separately identified as provided evidence.

| Retained output-extent condition | Native events | Native activity ms | Declared calls / forward / rank | Conditional candidates | Isolated reference ms / declared forward |
|---|---:|---:|---:|---:|---:|
| T=1024, H=7168 | 748 | 97.622454 | 187 | 82 | 20.522042879 |
| T=1, H=7168 | 14020 | 147.965865 | 187 | 41 | 1.408801979 |

The source declares 93 layers, two AttnRes points per layer and one final point: 187 per caller forward on a representative rank. The prefill declaration uses global rows 8192, TP8 local rows 1024 and DP4. DP4 is not multiplied into this single-rank event population.

Four hypothetical primary forwards give 748 calls and 82.088171514 ms of isolated reference activity. The retained 748 events total 97.622454 ms. Count equality does not prove four historical forwards or scalar flags, so no accuracy/error score is assigned.

The T=1 population has 14020 events. Seventy-five hypothetical forwards would have 14025 calls, leaving a difference of -5. It is not forced into complete steps. The provided integrated decode check uses global rows 8/local rows 1 on two layers; it does not establish global-row-1 SP support.

The T=1024 domain retains 25 primary flag combinations and 57 alternatives of unknown frequency; T=1 retains 25 primary combinations and 16 alternatives. Both descriptors in each extent class retain every candidate. Source line 47's four events are not bound to the first layer. Event durations never select optimization, materialization, residual-add, normalization, history or bank-write flags.

The same-image source establishes the six-input/three-output interface. Optional arguments fall back to nonempty tensors, and recorded shapes can describe backing allocations; neither reveals active prefix views or bank strides. Historical loaded binary, per-event flags, layer, replica and step remain unknown.

Independent checks: 211 package files match committed revision 2c0b339a, all 193 Python source hashes match the integration report, 12 retained image source hashes match, and four descriptor populations sum to 14768 events / 245.588319 ms. All primary counts and weighted candidate activities were recomputed.

Provided acceptance evidence separately reports 1850 tests passed in 257.61 s and 82 installed-wheel checks. The full 93-layer integration graphs were constructed and checked; engine executions use the first two original-geometry layers and the full DP cohort. These results were not rerun by this audit.

Inspect every scalar domain, per-candidate resource ledger and retained source identity in the JSON companion. The isolated reference excludes attention, FFN, SP collectives, embedding, logits/final normalization and host dispatch.

| Evidence | SHA256 |
|---|---|
| Candidate report: `/Users/maoxx241/code/sim-rewrite-20261027/data/verification/attnres-integrated-candidates-20261029.json` | `b084de238bdf58f34e2d3626298449d1ef3e5587a97f07ef6fa5a4ebe949b3fb` |
| Frontend integration: `/Users/maoxx241/code/sim-rewrite-20261027/data/verification/kimi-sp-attnres-integration-20261029.json` | `98ab10d0582b9aca63e79bf78500cfd323f0b4141e0c35ab8207f31fd8b0e7b1` |
| Capture boundary: `/Users/maoxx241/code/profiler/examples/structure/acceptance-20261029/kimi-attnres-boundary.json` | `59577f1625f593e2dabd8cdd48c44181e3521e4c8d0a33d1be5c65ac1b0674e3` |
| Retained CSV fixture: `/Users/maoxx241/code/profiler/tests/fixtures/kimi_grouped_attnres/a5_kimi_k3.csv` | `7b3f0cdf5bf2f318cfbdd3a5df4d95dc2e55092ed7ee2ed161106b534951bd16` |
| Delivery evidence: `/Users/maoxx241/code/sim-rewrite-20261027/data/verification/delivery-20261029-sp-attnres-paged.json` | `0ba75d9f55ef3f4cbf1724c6649f5f13e6a4de6928ebd161d6ee02a765868e35` |
| Installed wheel report: `/Users/maoxx241/code/sim-rewrite-20261027/data/verification/wheel-20261029-sp-attnres-paged.json` | `a97c06ae97ccf275029967da6f1ec033c675797c318894a3a5bf77a5e294bae1` |
