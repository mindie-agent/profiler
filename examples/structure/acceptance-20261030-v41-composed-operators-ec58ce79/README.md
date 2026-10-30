# V4.1 composed strict replay — ec58ce79 memory failure

This directory preserves the first complete c32 pilot against Sim ec58ce7921583967a50e803c78b962d90f8273b0. It reuses the retained c32 actual/mapping and the formal composed source case: B4, q1, context 2048, forty layers, DP8. No role filter or raw capture scan was used.

All fourteen attempted physical program workers failed the unchanged 512 MiB acceptance gate. No strict accuracy result is accepted, and the other six sources were not started. The full-family report retains failures and the original observed population. Earlier 5ec conditional references and the earlier c32 failure remain separate immutable artifacts.

The original replay controller retains per-program receipts in memory until the complete loop ends; therefore the repeated failure stderr was first available after the final pilot receipt was written. A subsequent single q_b diagnostic used the same worker and mapping with /usr/bin/time -l. Its exact command and stderr are retained in q_b-memory-probe.json:

- Exit status: 1, comparison_worker_exceeds_512_mib.
- Peak resident size: 596,688,896 bytes (569.05 MiB).
- Elapsed wall time: 7.79 seconds.
- No memory limit was increased and no failed output was counted as a comparison.

The parent Sim's smaller isolated measurement does not yet establish the actual profiler-worker footprint. The failure must be resolved with this retained command before expanding the seven-source strict campaign.
