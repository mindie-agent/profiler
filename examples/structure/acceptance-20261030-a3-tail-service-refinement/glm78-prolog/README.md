# Packed D656 prolog service increment

This independent increment extends the indexer/routing arm with the complete MlaPrologV3 population. The formal profiler parser now recognizes the retained packed cache: 512 INT8 latent bytes, 64 BF16 rotary elements and four FP32 scales give a 656-byte row. Full input/output tensor slots are retained, including typed empty separate rotary-cache outputs.

The existing Sim `mla_prolog` fusion has two exact active contracts: 57 calls per Forward without a query-normalization output, and 21 with INT8 query-normalization output plus FP32 scale. Each complete population supplies its own whole-call arithmetic mean to one local joint service. The selector uses the physical tensor view and output flag, never layer names. All previous response rules remain byte-for-byte unchanged; strict cohort admission and the 15% tolerance remain unchanged.

| Source | Ordinary / query-normalizing mean us | Sim Body ms | Error |
|---|---:|---:|---:|
| tpot30 c2 | 41.155689 / 41.220767 | 49.581701 | −13.9793% |
| tpot50 c2 | 41.123190 / 41.203505 | 49.554149 | −14.2916% |
| tpot88 c8 | 48.006266 / 52.947895 | 66.764459 | −4.0138% |

All three pass 15%; the two c2 cases still need refinement toward 10%. The small c8 regression is retained as the newest result. Full coverage remains 162 source Forwards / ten geometry groups, with 137 primary Forwards compared and seven groups explicitly deferred. Three fresh workers use Sim `21c30821d87a757bace8cf6b2fffea2536db643e`; no raw capture or device run is repeated.

Calibration is observed/in-sample. Unknown native scalar values, installed binary correspondence, pointer aliasing and transport concurrency remain separate from the measured joint service. Aggregate operator activity is not additive Body wall attribution. `prolog-service-populations.json` preserves all histograms, ABI identities, parser identity, exact contracts and rule matches. The Body arithmetic review passes 999 checks and the independent parameter/source review passes 95.

Reproduce with `build_glm78_prolog_service_cases.py`, then `replay_decode_forwards.py` using this directory's `decode-forward-prolog-service-cases.json`, `--geometry-limit 1`, `--prediction-timeout 90` and the pinned runtime commit. Set `PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure` and use the Sim `.venv/bin/python`.
