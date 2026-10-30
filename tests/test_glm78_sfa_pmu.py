"""Real GLM78 SFA PMU samples preserve signed concurrent-pipeline evidence."""
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
spec = importlib.util.spec_from_file_location('sfa_pmu', ROOT / 'examples/structure/collect_glm78_sfa_pmu.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SAMPLES = json.loads((ROOT / 'tests/fixtures/decode_forward/glm78_sfa_pmu.json').read_text())


def test_actual_small_query_pipeline_sum_and_max_remain_distinct_signed_constraints():
    sample = SAMPLES[0]['examples'][0]
    result = module.paired_diagnostics(sample['raw_fields'], sample['duration_ns'])
    assert result['aic'] == {'sum_minus_elapsed_us': Decimal('-19.316'),
                             'max_minus_elapsed_us': Decimal('-75.720')}
    assert result['aiv'] == {'sum_minus_elapsed_us': Decimal('18.921'),
                             'max_minus_elapsed_us': Decimal('-50.500')}


def test_actual_large_query_overlap_is_not_an_additive_wall_cost():
    sample = SAMPLES[2]['examples'][0]
    result = module.paired_diagnostics(sample['raw_fields'], sample['duration_ns'])
    assert result['aic'] == {'sum_minus_elapsed_us': Decimal('107.083'),
                             'max_minus_elapsed_us': Decimal('-124.670')}
    assert result['aiv'] == {'sum_minus_elapsed_us': Decimal('161.511'),
                             'max_minus_elapsed_us': Decimal('-72.901')}
