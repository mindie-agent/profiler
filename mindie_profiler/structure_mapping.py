"""Associate measured occurrences with a shared, declared model structure.

[Role] Consume sim structure data and attach independently measured events.
[Invariants] Tensor equality is a candidate, never proof of layer identity.
  Explicit occurrence evidence or an unambiguous Host connection can bind a
  node. Fused events retain inclusive attribution and are counted once in the
  window union. No prediction or measured duration selects a structural node.
[Timeouts & Locks] Bounded metadata files and event-window budget; no locks.
[Side-Effect Policy] Reads caller-selected JSON only; no sim import or writes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from .accounting import merge_intervals
from .events import ProfilerUsageError
from .structure_subgraphs import StructureTargets
from .structure_cohorts import CohortAccumulator

from .structure_mapping_helpers import (
    MAX_METADATA_BYTES, SCHEMA, _DTYPE_TOKENS, _event_inputs, _event_key,
    _event_raw_identity, _event_signature, _freeze, _native_call_signature_match,
    _seal_digest, _shared_kv_candidates, _snapshot_structure_carrier, _task_key,
    _union_ns, _verify_graph_id, read_metadata,
)
from .structure_mapping_mapper import StructureMapper

def map_structure(observations: Sequence[Any], structure, *, bindings=None, correlations=None,
                  module_traces=None, mapping_limit=200, max_events=100_000, phase=None):
    from .module_evidence import ModuleEvidence

    module_evidence = (ModuleEvidence(module_traces, observations, max_records=max_events)
                       if module_traces else None)
    mapper = StructureMapper(
        structure, bindings=bindings, correlations=correlations,
        mapping_limit=mapping_limit, max_events=max_events,
        phase=phase, module_evidence=module_evidence,
    )
    return mapper.finish([mapper.map_window(observation) for observation in observations])
