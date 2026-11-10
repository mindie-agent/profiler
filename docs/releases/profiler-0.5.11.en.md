# mindie-profiler 0.5.11

[中文](profiler-0.5.11.md)

This maintenance release repairs dependency ordering and automatic-update delivery. It pairs with formally published, old-updater-verified sim 0.9.10 and retains the 0.5.10 analysis engine. Historical captures and accuracy experiments are not relabeled as new measurements.

- First-party dependencies must pass the released client's complete Release validator; an existing formal tag alone is insufficient.
- Protected-main publication exposes an immutable Release only after packages, benchmarks, checksums and actual upgrade acceptance succeed.
- The unmodified released updater discovers the newest components, builds a real isolated generation and probes its CLI. A second upgrade uses the normal public source.
- Historical A3 replay compares physical hardware parameters without making explanatory assumptions or provenance wording an applicability condition. Rates, kernel boundaries and topology remain fully checked.
- A2 replay tests declare the Vector rate recorded in the retained profile, preserving historical input as current SKU defaults evolve. Cross-platform capture enumeration deduplicates root-relative paths with directory boundaries.
- Linux prediction workers report their current executable's `VmHWM`, excluding the launcher's retained pre-exec peak. The 512 MiB limit remains enforced; a real parent/child process regression also verifies that releasing memory preserves the recorded peak.
- Latest-by-default selection and monotonic upgrades remain unchanged. The release carries its actual test, benchmark and old-updater evidence.
