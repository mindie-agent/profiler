"""Actual low-M replay projections keep timings while declaring source rank scope."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'examples/structure/body.py'
SPEC = importlib.util.spec_from_file_location('body_source_routing_projection', MODULE)
BODY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BODY)
FIXTURE = ROOT / 'tests/fixtures/pipeline/source_routing_projection.json'


def test_real_source_prediction_keeps_math_and_explicit_rank_semantics():
    row = json.loads(FIXTURE.read_text())
    predicted = deepcopy(row['prediction'])
    observed = row['observed']
    old = BODY.compare_body_forward(predicted, observed)
    old_layers = BODY.compare_layers(predicted, observed)
    predicted['source_routing_declaration'] = BODY.source_routing_declaration(row['kernels'])
    new = BODY.compare_body_forward(predicted, observed)
    new_layers = BODY.compare_layers(predicted, observed)
    assert {k:v for k,v in old.items() if k != 'assumptions'} == {k:v for k,v in new.items() if k != 'assumptions'}
    assert {k:v for k,v in old_layers.items() if k != 'assumptions'} == {k:v for k,v in new_layers.items() if k != 'assumptions'}
    assert 'asymmetric' in new['assumptions'][-1]
    assert 'exchange symmetry' not in new_layers['assumptions'][-1]
    assert new['passed'] is True
    assert BODY.source_routing_declaration({}) is None
