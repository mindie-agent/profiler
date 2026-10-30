"""Retained Qwen cross-TP functions must execute on Engine's native work axes."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from service_evidence import predict_service_domains, service_regimes


def test_frozen_matrix_function_survives_inventory_to_engine_projection():
    pytest.importorskip('mindie_sim')
    from mindie_sim.prediction.operator_analysis import operator_costs, target_graphs
    from mindie_sim.prediction.structure import parse_case

    retained = json.loads((ROOT / 'tests/fixtures/retrospective_heldout/'
                            'qwen-matrix-coordinate-export.json').read_text())
    frozen, points = retained['frozen_model'], retained['points']
    before = deepcopy(frozen)
    rules = service_regimes(frozen, points)['rules']
    declaration = retained['case']
    declaration['runtime']['kernels']['service_regimes'] = rules
    case = parse_case(declaration)
    graph = target_graphs(case, phase='decode', tokens=4, sequences=4,
                          context=4096, scope='body')[0]
    for point in points:
        op = next(op for op in graph if op.op_id == point['axes']['op_id'])
        assert op.flops == point['axes']['work']['flops']
        assert op.hbm_bytes == point['axes']['work']['hbm_bytes']
        result = operator_costs(case, (op,))
        records = result['operators'][0]['basis']['service_regimes']
        record = next(record for record in records
                      if record['id'] == 'frozen-' + point['domain_id'])
        assert record['queries'] == {'observable_response': 1}
        expected = predict_service_domains(frozen, point)['predicted_us']
        assert record['response_us_min'] == pytest.approx(expected)
        assert record['response_us_max'] == pytest.approx(expected)
        assert record['provenance']['frozen_model_sha256'] == frozen['sha256']
    assert frozen == before
