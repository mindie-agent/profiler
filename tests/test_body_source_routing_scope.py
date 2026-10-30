"""Actual low-M replay projections keep timings while declaring source rank scope."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'examples/structure/body_forward_comparison.py'
SPEC = importlib.util.spec_from_file_location('body_source_routing_projection', MODULE)
BODY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BODY)
DIRECTORY = ROOT / 'examples/structure/acceptance-20261030-service-kimi-v41'


def test_real_eight_source_predictions_keep_math_and_explicit_rank_semantics():
    report = json.loads((DIRECTORY / 'decode-forward-source-routing-84d80b40-replay.json').read_text())
    manifest = json.loads((DIRECTORY / 'decode-forward-source-routing-84d80b40-cases.json').read_text())
    inputs = {r['case_id']: r for r in manifest['cases']}
    for row in report['cases']:
        case = json.loads(Path(inputs[row['source_case_id']]['sim_case_path']).read_text())
        predicted = deepcopy(row['prediction'])
        observed = row['observed']
        old = BODY.compare_body_forward(predicted, observed)
        old_layers = BODY.compare_layers(predicted, observed)
        predicted['source_routing_declaration'] = BODY.source_routing_declaration(case['runtime']['kernels'])
        new = BODY.compare_body_forward(predicted, observed)
        new_layers = BODY.compare_layers(predicted, observed)
        assert {k:v for k,v in old.items() if k != 'assumptions'} == {k:v for k,v in new.items() if k != 'assumptions'}
        assert {k:v for k,v in old_layers.items() if k != 'assumptions'} == {k:v for k,v in new_layers.items() if k != 'assumptions'}
        assert 'asymmetric' in new['assumptions'][-1]
        assert 'exchange symmetry' not in new_layers['assumptions'][-1]
        assert new['passed'] is True
        # The old arm does not get source semantics from a case/model name.
        assert BODY.source_routing_declaration({}) is None
