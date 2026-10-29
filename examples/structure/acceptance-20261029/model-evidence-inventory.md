# Model profiling evidence inventory

Audited on 2026-10-29. The accompanying `model-evidence-inventory.json` records
absolute source paths, independently retained run configuration, raw counts and
hardware uncertainty. This inventory is source discovery, not a declaration that
every event has already been mapped to a model layer.

| Model / hardware | Retained raw evidence | Host / module evidence | Independent run geometry |
| --- | --- | --- | --- |
| GLM-5.3 W4A8 / A3 | 16 full-model rank-0 `raw/kernels/*.csv.gz`; representative prefill 2,392 rows, decode 166,204 rows | No retained Host DB or module trace alongside exports | Model config, TP8 recipe, p4096/o1/c1 prefill, p4096/o256/c1 decode, metrics gate receipt |
| DeepSeek-V4-Flash W8A8 / A3 | Full-model `v4f-prefill/raw/pre4096.kernel_details.csv`, 4,064 rows; other lengths and c4 captures retained | Exported kernels only | TP8/EP8/DP1, p4096/o1/c1, batch8192, exact model path and profiler/export scripts |
| DeepSeek-V4-Pro W4A8 / A3 | Full-model `v4pro-prefill/raw/pre4096.kernel_details.csv`, 24,271 rows; other lengths/c4 retained | Exported kernels only | TP16/EP16/DP1, p4096/o1/c1, batch1024, exact model path and profiler/export scripts |
| Kimi-K3 W4A8 MXFP / A5 | `k3lc-os1.tgz` contains full-model `raw/prof-export/op_summary_20261023053244.csv`, 286,988 Device0 rows | Retained trace is API-process Python only; no model-module or kernel-flow events | TP8/DP4/EP32, p32768/o64/c1, seed4131, batch8192; model config not retained |
| GLM-4.5 historical / unresolved A2-or-A3 SKU | Original DB, 252,644 TASK rows | 154,106 PyTorch APIs, 48,964 CANN APIs, connection IDs; modules disabled | No independent model config/request geometry found in inspected export |
| DeepSeek V4 historical / unresolved exact hardware SKU | Four representative DB groups, 27,332 / 241,614 / 147,921 / 213,225 TASK rows | Real PyTorch/CANN API and connection tables; modules disabled | Parallel-group metadata exists; folder workload labels are not independently verified |
| GLM-5.3 / A5 inspected archives | Serving metrics/request summaries only | No raw kernel CSV/DB/device trace in the three inspected archives | Serving geometry alone cannot establish kernel acceptance |
| DeepSeek V4.1 / A5 inspected campaign roots | Serving metrics only | No raw kernel CSV/DB in inspected roots | Not kernel acceptance |
| Kimi-shaped KDA/GDN/MLA / A3 and A5 | Standalone operator DB/CSV captures | Primitive Host/device records | Useful ABI evidence; not a full Kimi model run |

Here, "full-model" means all retained kernel records from a serving rank/device
within a capture window. It does not mean all ranks, every generated token, or
proven layer-occurrence identity. No full-model Kimi A3 kernel capture was found
in the inspected roots; the existing KDA/GDN/MLA captures are primitives.

## Hardware evidence

GLM53 A3 includes an actual npu-smi log with eight cards, two physical dies per
card, Phy-ID 0..15, and 64 GiB per die. Its recipe identifies host
192.168.13.165. DeepSeek Flash/Pro have same-model, same-day serving-campaign
npu-smi logs with that topology and separate profiler-container recipes naming
the same host. The hardware log is corroborating evidence, not a table embedded
in each exported kernel CSV.

Kimi A5 has same-rack06-os1 campaign npu-smi output naming Ascend950DT with
98,304 MiB per device, plus an A5 serving recipe. Historical GLM45 and all four
DeepSeek DB groups report the generic `Ascend910B` name. GLM45 records 20 AIC /
40 AIV at1650; three DeepSeek groups record24 /48 at1800. Those resource records
and an A3-looking folder are insufficient to establish the exact historical
product topology; this inventory leaves that SKU unresolved.

## Kimi archive and phase boundary

The source archive is
`/Volumes/data/mindie-sim-data/a5/2026-10-23/kimi-k3-longctx/k3lc-os1.tgz`.
Its op_summary member is110,031,770 bytes. Its header uses `OP Type`, `Op Name`,
`Task Type`, `Task Start Time(us)` and `Task Duration(us)`, plus input/output
shape, dtype, layout and PMU fields.

The raw count is286,988, not the1,482,236 claimed by a retained derived summary.
The request receipt independently confirms p32768/o64/c1. The capture mixes
prefill and decode; the retained phase reports split by client TTFT or tensor
patterns and disagree. They must not supply exact per-event phase identities.
The122,925,642-byte decompressed trace was streamed:425,759 `python_function`
events and one `Trace`, with no module hierarchy identifiers or device kernels.

Only the op_summary member was streamed to
`/tmp/mindie-body-profiling-kimi-op-summary.csv` for full replay; no other archive
member was copied. Its SHA256 is
`ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648`.
The original archive SHA256 is
`8b74c09cfdbdb14d010f7c941b4911abc88e865a9d625e88813f4096ed91a00d`.

Eight unchanged original records are retained in
`tests/fixtures/body_attention/kimi_a5_full_model.csv`. Its companion provenance
records both hashes, original row/line numbers, stream/task identities and
full-source kind counts. The slice is contract-test evidence, not a replacement
for the full capture.
