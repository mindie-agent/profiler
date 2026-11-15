"""Re-declare one complete real TensorMove population through the core accumulator."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import StructureMapper

FIXTURE = Path(__file__).parent / 'fixtures/pipeline/tensor_move_cohort.json'


def retained_case():
    pytest.importorskip('mindie_sim')
    path = case_path('qwen35-35b-a5-tp4-c128-mc2-tp-source-complete.json')
    doc = json.loads(path.read_text())
    doc['model']['layers'] = 4
    return doc


@lru_cache(maxsize=16)
def _cached_export(case_canonical: str, geometry_canonical: str) -> dict:
    from mindie_sim.structure import export_structure
    return export_structure(json.loads(case_canonical), **json.loads(geometry_canonical))


def mapping_for_case(case):
    saved = json.loads(FIXTURE.read_text())
    execution = saved['declared_execution']
    geometry = {k: execution[k] for k in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    manifest = deepcopy(_cached_export(
        json.dumps(case, sort_keys=True),
        json.dumps(geometry, sort_keys=True),
    ))
    mapper = StructureMapper(manifest)
    original = saved['cohort']
    declared_layers = int(manifest['execution']['software']['pp_layer_partition'][0])
    target_ids = [
        tid for tid in original['target_ids']
        if declared_layers >= 40 or any(f'.l{i}.' in tid for i in range(declared_layers))
    ]
    # Complete retained candidate set, tensor contract and work must all survive.
    assert len(target_ids) == 4 * declared_layers
    assert set(target_ids) <= mapper.target_index.all.keys()
    for identifier in target_ids:
        target = mapper.target_index.all[identifier]
        assert json.dumps(target['contract']) == json.dumps(original['contract'])
    window = saved['window']
    identity = window['source_identity']
    source = SourceRef(window['rank_id'], 0, 'csv', identity['path'], 'retained TensorMove',
                       identity['sha256'], identity['size_bytes'], 'retained', 'cohort')
    bounds = window['window']
    observed = Observation(window['rank_id'], 0, Window(bounds['start_ns'], bounds['end_ns']),
                           None, [], source, QueryStats(window['rank_id'], 'retained'))
    accumulator = CohortAccumulator(manifest['graph_id'], mapper.target_index, observed,
                                    execution=manifest['execution'])
    declaration, reason = accumulator._cohort(target_ids)
    assert reason is None
    cohort = {**deepcopy(original), **declaration}
    cohort['multiplicity'] = {
        **cohort['multiplicity'],
        'declared_instances': declaration['declared_instance_count'],
        'calls_per_declared_instance': cohort['event_count'] / declaration['declared_instance_count'],
    }
    return manifest, {'schema_version': 'mindie-profile-structure-mapping/1',
                      'graph_id': manifest['graph_id'], 'declared_execution': manifest['execution'],
                      'windows': [{**window, 'cohorts': [cohort]}]}
