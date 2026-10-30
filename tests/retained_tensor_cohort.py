"""Re-declare one complete real TensorMove population through the core accumulator."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import StructureMapper

FIXTURE = Path(__file__).parent / 'fixtures/pipeline/tensor_move_cohort.json'


def retained_case():
    sim = pytest.importorskip('mindie_sim')
    path = case_path('qwen35-35b-a5-tp4-c128-mc2-tp-source-complete.json')
    return json.loads(path.read_text())


def mapping_for_case(case):
    from mindie_sim.structure import export_structure

    saved = json.loads(FIXTURE.read_text())
    execution = saved['declared_execution']
    geometry = {k: execution[k] for k in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    manifest = export_structure(case, **geometry)
    mapper = StructureMapper(manifest)
    original = saved['cohort']
    # Complete retained candidate set, tensor contract and work must all survive.
    assert set(original['target_ids']) <= mapper.target_index.all.keys()
    for identifier in original['target_ids']:
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
    declaration, reason = accumulator._cohort(original['target_ids'])
    assert reason is None
    cohort = {**deepcopy(original), **declaration}
    return manifest, {'schema_version': 'mindie-profile-structure-mapping/1',
                      'graph_id': manifest['graph_id'], 'declared_execution': manifest['execution'],
                      'windows': [{**window, 'cohorts': [cohort]}]}
