"""Original measured-entry recovery for the 731 zero-shot cells.

[Role] Join each portable cell ID to its one unaltered producer JSON under the
  retained workstream roots and project only the fields that the producer
  actually recorded: per-request TPOT, TTFT, completion-token count and the
  measured decode-step interval count.
[Invariants] The exact producer record is authoritative for client TPOT/TTFT;
  a divergent stored value is replaced and marked in source_conflict, never
  chosen because its error is smaller. Emitted completion tokens are request
  metadata and never override an inferred device forward/step count. TTFT is
  kept when TPOT is absent; ITL is not substituted for TPOT.
[Timeouts & Locks] Bounded synchronous JSON reads; no network, subprocess,
  sleep or lock. The tag index is O(number of retained measured JSON files).
[Side-Effect Policy] Read-only; returns new frozen cell records and provenance.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_ROOTS = (
    Path('/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107'),
    Path('/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack08-20261107'),
)
@dataclass(frozen=True)
class OriginalObservation:
    cell_id: str
    measured_path: str
    raw_tag: str
    tpot_ms: float | None
    ttft_ms: float | None
    completion_tokens: tuple[int, ...]
    request_tokens: int
    max_tokens: int
    tpot_field: str
    ttft_field: str


def _float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if out == out and out >= 0.0 else None

def _index(roots: Sequence[Path]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        for path in sorted((*base.glob('*/measured/*.json'), *base.glob('out/*/measured/*.json'))):
            tag = path.stem
            if tag in found and found[tag] != path:
                raise ValueError(f'duplicate_measured_tag:{tag}:{found[tag]}:{path}')
            found[tag] = path
    return found

def _observation(cell_id: str, path: Path) -> OriginalObservation | None:
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or str(raw.get('tag') or '') != cell_id:
        return None
    streams = [item for item in (raw.get('streams') or ()) if isinstance(item, Mapping)]
    completion = tuple(int(item.get('completion_tokens') or 0) for item in streams)
    tpot_field, ttft_field = '', ''
    tpot = _float(raw.get('tpot_mean_s'))
    if tpot is not None:
        tpot_field = 'tpot_mean_s'
    else:
        tpot = _float(raw.get('tpot_p50_s'))
        tpot_field = 'tpot_p50_s' if tpot is not None else ''
    ttft = _float(raw.get('ttft_mean_s'))
    if ttft is not None:
        ttft_field = 'ttft_mean_s'
    else:
        ttft = _float(raw.get('ttft_p50_s'))
        ttft_field = 'ttft_p50_s' if ttft is not None else ''
    if tpot is None and ttft is None:
        return None
    return OriginalObservation(
        cell_id=cell_id, measured_path=str(path), raw_tag=str(raw.get('tag') or path.stem),
        tpot_ms=None if tpot is None else tpot * 1000.0,
        ttft_ms=None if ttft is None else ttft * 1000.0,
        completion_tokens=completion,
        request_tokens=max(completion, default=0), max_tokens=int(raw.get('max_tokens') or 0),
        tpot_field=tpot_field, ttft_field=ttft_field)
def load_observations(cell_ids: Iterable[str], roots: Sequence[Path] = DEFAULT_ROOTS) -> dict[str, OriginalObservation]:
    index = _index(roots)
    result: dict[str, OriginalObservation] = {}
    for cell_id in cell_ids:
        tag = str(cell_id).split(':')[-1]
        if (path := index.get(tag)) is not None and (obs := _observation(tag, path)) is not None:
            result[cell_id] = obs
    return result

def apply_original_observations(cells: Sequence[Any], roots: Sequence[Path] = DEFAULT_ROOTS) -> list[Any]:
    """Use the exact producer record for client fields; never trust a stale copy."""
    observations = load_observations((cell.spec.cell_id for cell in cells), roots)
    out = []
    for cell in cells:
        obs = observations.get(cell.spec.cell_id)
        if obs is None:
            out.append(cell)
            continue
        conflicts = []
        if obs.tpot_ms is not None and cell.tpot_ms is not None and abs(cell.tpot_ms - obs.tpot_ms) > 1e-6:
            conflicts.append('tpot')
        if obs.ttft_ms is not None and cell.ttft_ms is not None and abs(cell.ttft_ms - obs.ttft_ms) > 1e-6:
            conflicts.append('ttft')
        out.append(replace(
            cell,
            tpot_ms=obs.tpot_ms if obs.tpot_ms is not None else cell.tpot_ms,
            ttft_ms=obs.ttft_ms if obs.ttft_ms is not None else cell.ttft_ms,
            request_tokens=obs.request_tokens if hasattr(cell, 'request_tokens') else 0,
            source_conflict=','.join(conflicts), source_measured=obs.measured_path))
    return out
def cell_entry(cell: Any, comparisons: Sequence[Any], required: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """Stable per-cell ABI for C: present/missing/pass states, never aggregate error copies."""
    by_key = {(item.level, item.target): item for item in comparisons}
    targets = []
    for level, target in required:
        item = by_key.get((level, target))
        if item is None or item.measured_ms <= 0:
            targets.append({'level': level, 'target': target, 'status': 'uncovered', 'samples': 0, 'errors': [], 'uncancelled_ms': 0.0})
            continue
        errors = [detail[3] for detail in (item.step_details or ((0, item.measured_ms, item.predicted_ms, item.signed_error),))]
        finite = [float(value) for value in errors]
        targets.append({
            'level': level, 'target': target,
            'status': 'pass' if all(value == value and abs(value) <= 0.1 for value in finite) and item.uncancelled_ms / item.measured_ms <= 0.1 else 'above_10pct',
            'samples': len(finite), 'errors': finite,
            'uncancelled_ms': float(item.uncancelled_ms)})
    return {
        'cell_id': cell.spec.cell_id, 'phase': cell.spec.phase,
        'request_tokens': int(getattr(cell, 'request_tokens', 0)),
        'tpot_ms': cell.tpot_ms, 'ttft_ms': cell.ttft_ms,
        'trace_quality': cell.trace_quality,
        'source_conflict': str(getattr(cell, 'source_conflict', '')),
        'source_measured': str(getattr(cell, 'source_measured', '')), 'targets': targets,
    }
