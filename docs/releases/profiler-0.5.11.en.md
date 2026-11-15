# mindie-profiler 0.5.11

[中文](profiler-0.5.11.md)

This maintenance release hardens dependency ordering and automatic-update delivery, pairing with [`mindie-sim 0.9.10`](https://github.com/mindie-agent/sim) after end-to-end upgrade verification from previously released updater clients. The core analysis engine is unchanged from `0.5.10`, and prior captures and accuracy experiments are preserved as historical artifacts rather than relabeled as new measurements.

- **Full release validation for first-party dependencies**: Upstream first-party dependencies must pass the released client's full Release validator (packages, checksums, and release metadata); a formal Git tag alone is no longer sufficient.
- **Verify-before-expose publication gate**: Releases cut from `main` remain unpublished until wheel builds, benchmark gates, checksums, and live upgrade acceptance all succeed, then publish as immutable Releases.
- **Two-stage live updater acceptance**: An unmodified previously released updater first discovers the candidate components in an isolated staging environment, builds a complete runtime generation, and verifies the CLI; once published, a second upgrade check verifies delivery from the public release channel.
- **Physics-only applicability checks for historical A3 replay**: Historical A3 replay validates hardware parameters, device rates, kernel boundaries, and parallel topology without treating explanatory notes or provenance wording changes as physical mismatches.
- **Explicit A2 historical Vector rate & path-boundary deduplication**: A2 replay tests explicitly pass the Vector rate recorded in the retained profile so evolving SKU defaults never alter historical test inputs; cross-platform capture enumeration deduplicates root-relative paths on true directory boundaries rather than raw string prefixes.
- **Accurate post-`exec` `VmHWM` peak memory accounting on Linux**: Linux prediction worker subprocesses now report `VmHWM` for the current executable image rather than inheriting the parent launcher's pre-`exec` high-water mark. The `512 MiB` working-set ceiling remains enforced, backed by a real parent/child regression test confirming peak retention after deallocation.
- **Unchanged monotonic upgrade policy**: Latest-by-default resolution and monotonic version guards remain unchanged, and test, benchmark, and updater-upgrade receipts ship alongside the release.
