"""Declarative benchmark profile loader for ``mindie_profiler.bench``.

[Role]
  Load and cache ``bench_profiles.json`` once per process so protocol budgets,
  CANN format codes, sweep dimensions and held-out split axes share a single
  auditable JSON source without scattering inline numeric literals across
  Python modules.

[Invariants]
  * Pure stdlib loader: never imports ``torch``, ``torch_npu`` or ``mindie_sim``.
  * Fails closed if ``bench_profiles.json`` is missing or carries an unknown
    schema tag.

[Timeouts & Locks]
  Single small package-file read cached via ``functools.lru_cache``; no locks.

[Side-Effect Policy]
  Read-only access to the co-located ``bench_profiles.json`` resource.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping

from ..events import ProfilerUsageError

PROFILES_SCHEMA = "mindie-bench-profiles/1"
_PROFILES_PATH = Path(__file__).with_name("bench_profiles.json")


@lru_cache(maxsize=1)
def load_bench_profiles() -> Mapping[str, Any]:
    """Read and validate the packaged benchmark profile manifest."""
    try:
        payload = json.loads(_PROFILES_PATH.read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError) as exc:
        raise ProfilerUsageError(f"bench_profiles_invalid: {exc}") from exc
    if not isinstance(payload, Mapping) or payload.get("schema") != PROFILES_SCHEMA:
        raise ProfilerUsageError(
            f"bench_profiles_schema_mismatch: expected {PROFILES_SCHEMA}")
    return payload


def profile_section(name: str) -> Mapping[str, Any]:
    """Return one top-level section from ``bench_profiles.json``."""
    section = load_bench_profiles().get(name)
    if not isinstance(section, Mapping):
        raise ProfilerUsageError(f"bench_profiles_section_missing: {name}")
    return section


__all__ = ["PROFILES_SCHEMA", "load_bench_profiles", "profile_section"]
