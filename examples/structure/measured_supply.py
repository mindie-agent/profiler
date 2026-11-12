"""Normal measured-supply cache key and case application helpers."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping


def supply_key(value: Any) -> str:
    if isinstance(value, Mapping):
        return hashlib.sha256(json.dumps(value, sort_keys=True,
                                         default=str).encode()).hexdigest()
    path = Path(value).expanduser(); stat = path.stat()
    return f"{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"


def apply_supply(value: Any, raw_case: dict, hardware: str | None = None) -> dict:
    from mindie_sim.observations.calibration import apply_profiler_supply
    machine = raw_case.get("machine") or {}
    chosen = hardware or machine.get("hardware_key") or machine.get("sku") or ""
    return apply_profiler_supply(raw_case, value, recipe="output",
                                 hardware=chosen, required=False)
