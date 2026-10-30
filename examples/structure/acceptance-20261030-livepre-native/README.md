# A3 GLM Flash livepre runtime and native fusion controls

Two retained captures contain 181 complete Forwards across 17 geometries. The
83 Forward calls in the two principal populations are freshly predicted; the
15 smaller geometries remain visible and deferred. No CSV was reread and no
device workload ran.

| Case | Main Forward calls | Real mean ms | Unchanged declaration at a961c114 | A3 native fusion ms | Error |
|---|---:|---:|---:|---:|---:|
| c4, q6/B4/M24 | 46 | 29.761551 | 37.342291 | 31.440509 | +5.64% PASS |
| c16, q6/B16/M96 | 37 | 41.069081 | 63.851407 | 50.830453 | +23.77% FAIL |

The runtime-only baseline equals the preceding selected predictions. The
second arm selects the existing A3 HCPre/HcPost source profiles and INT8
grouped-gate-up/activation/quantization fusion. Each graph has 222 native
invocations: 90 HCPre, 90 HCPost and 42 grouped gate-up calls. Source-controlled
internal materializations and launches are eliminated by Sim's shared fusion
frontend. Existing response parameters remain unchanged; no Body residual was
used to set a rate.

The source implementation is conditional on the declared native program;
captured binary identity and expert group-list values are not established.
The INT8 sparse attention declaration and symbolic accepted-state conditions
are retained. A5 HC profiles and A3 D656 prolog changes are not substituted for
these cases' own native boundaries.

The c16 scheduled sparse-attention batch remains a large discrepancy: 11 calls
at 649.134 us compared with the retained native family mean of about 377.58 us.
Its scheduled sum is 7.140 ms versus 4.153 ms of observed native activity.
These are service/interval diagnostics, not additive attribution of the entire
Body wall-clock error. The follow-up `native_role_diagnostic.py` uses Sim's
explicit fusion-role metadata on package fingerprint `c347250c5f5e` and preserves
the same Body predictions. It distinguishes 42 grouped gate-up and 42 down calls
from the 90 HCPre and 90 HCPost calls.

For c16, grouped gate-up contributes +5.833 ms of scheduled-minus-observed
activity and down +2.939 ms; sparse attention adds +2.987 ms. HCPre and HCPost
instead undershoot by 1.263 and 0.547 ms. Reducing HC to close the Body error
would contradict this evidence. Corresponding c4 grouped differences are
+2.967 and +1.399 ms. The complete native family means and multiplicities are
checked against retained integer histograms; full-population ABI and expert
group-list values remain separate unresolved evidence, not inferred from time.

`prepare_cases.py` reproduces the two declarations over unchanged source-pinned
extractions. `native-independent-review.json` verifies 455 population,
identity, endpoint and unrounded tolerance invariants with zero failures.
Both successful and failed arms enter the ordered main scoreboard.
