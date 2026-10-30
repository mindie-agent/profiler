"""Real livepre populations replace their prior floor without double counting."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


def test_complete_livepre_joint_domains_replace_only_the_same_native_floor(tmp_path, monkeypatch):
    pytest.importorskip('mindie_sim.prediction.service_regimes')
    root = Path(__file__).resolve().parents[1]
    directory = root / 'examples/structure/acceptance-20261030-livepre-native'
    sys.path.insert(0, str(directory.parent))
    spec = importlib.util.spec_from_file_location('livepre_joint_builder', directory / 'build_joint_service.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    before = json.loads((directory / 'decode-forward-native-cases.json').read_text())
    (tmp_path / 'decode-forward-native-cases.json').write_text(json.dumps(before))
    monkeypatch.setattr(builder, 'HERE', tmp_path)
    builder.build('metadata-only-test')
    result = json.loads((tmp_path / 'joint-service/decode-forward-cases.json').read_text())
    populations = json.loads((tmp_path / 'joint-service/observed-populations.json').read_text())
    for old, new, population in zip(before['cases'], result['cases'], populations['cases']):
        source = json.loads(Path(old['sim_case_path']).read_text())
        generated = json.loads(Path(new['sim_case_path']).read_text())
        rules = generated['runtime']['kernels']['service_regimes']
        joint = [r for r in rules if r.get('execution')]
        replaced = population['replaced_same_native_completion_floors']
        retained = [r for r in rules if not r.get('execution')]
        prior = source['runtime']['kernels'].get('service_regimes', [])
        assert retained == [r for r in prior if r not in replaced]
        assert [r['id'] for r in replaced] == (
            ['groupedmatmul-expert_down-observed-0'] if '-c4-' in old['case_id'] else [])
        assert sorted(r['provenance']['expected_rule_hits'] for r in joint) == [11, 42, 42, 90, 90]
        for r in joint:
            assert r['response']['fixed_us'] == r['provenance']['observed_native_elapsed_us']['mean_us']
            assert r['provenance']['observed_native_elapsed_us']['count'] == (
                r['provenance']['expected_rule_hits'] * r['provenance']['forward_count'])
        # Case metadata/queue declarations do not alter the source graph or its
        # existing communication, convolution and recurrence choices.
        original_kernels = deepcopy(source['runtime']['kernels'])
        new_kernels = deepcopy(generated['runtime']['kernels'])
        original_kernels.pop('service_regimes', None)
        new_kernels.pop('service_regimes', None)
        assert new_kernels == original_kernels
        assert generated['model'] == source['model']
        assert generated['workload'] == source['workload']
        assert new['replay_input_pins']['extraction'] == old['replay_input_pins']['extraction']
