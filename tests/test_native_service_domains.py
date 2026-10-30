"""Retained whole-native populations survive selected fusion resource boundaries."""
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim", reason="companion Sim acceptance tools require the optional runtime")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from price_native_service_domains import observed_population, selected_programs
from build_qwen_a3_service_cases import physical_ops


def test_livepre_complete_populations_select_actual_fused_resource_programs():
    pytest.importorskip('mindie_sim')
    from mindie_sim.structure import export_structure
    root = ROOT / 'examples/structure/acceptance-20261030-livepre-native/joint-service'
    manifest = json.loads((root / 'decode-forward-cases.json').read_text())
    row = next(r for r in manifest['cases'] if r['case_id'].endswith('c4-livepre'))
    raw = json.loads(Path(row['sim_case_path']).read_text())
    geometry = row['replay_input_pins']['primary_geometry']
    case, ops = physical_ops(raw, geometry)
    structure = export_structure(case, phase='decode', tokens=geometry['tokens_per_sequence'],
        context=geometry['context_tokens'], sequences=geometry['sequences_per_replica'], scope='body')
    resources = {n['op_id']: n for n in structure['resource_operators']}
    complete = {}
    for rule in raw['runtime']['kernels']['service_regimes']:
        if rule.get('execution', {}).get('kind') != 'joint_native':
            continue
        measured = observed_population('livepre', row['case_id'], rule)
        selected = selected_programs(rule, case, ops)
        count = sum(measured['histogram'].values())
        assert count == len(selected) * measured['forward_count']
        assert measured['native_abi'] is None
        assert measured['evidence_strength'] == 'source_symbol_retained_group'
        if measured['native'] in {'HcPost', 'HcPre', 'GroupedMatmulSwigluQuant'}:
            assert all(op.op_id in resources for op, _ in selected)
        complete[measured['native']] = count
    assert complete == {'HcPre':4140,'HcPost':4140,'GroupedMatmulSwigluQuant':1932,
                        'GroupedMatmul':1932,'KvQuantSparseFlashAttentionVllm':506}


def test_glm78_full_v2_ABI_keeps_whole_selected_native_population():
    root = ROOT / 'examples/structure/acceptance-20261030-glm78-native-v2-service'
    manifest = json.loads((root / 'decode-forward-glm78-native-v2-cases.json').read_text())
    row = next(r for r in manifest['cases'] if r['case_id'].endswith('tpot30_c2'))
    raw = json.loads(Path(row['sim_case_path']).read_text())
    selected = [r for r in raw['runtime']['kernels']['service_regimes']
                if r.get('provenance', {}).get('native_operator_type') in
                {'MoeDistributeDispatchV2','MoeDistributeCombineV2'}]
    assert len(selected) == 2
    for rule in selected:
        measured = observed_population('glm78', row['case_id'], rule)
        abi = measured['native_abi']
        assert measured['evidence_strength'] == 'full_native_abi'
        assert sum(measured['histogram'].values()) == 3300
        assert measured['forward_count'] == 44 and len(measured['layer_ids']) == 75
        assert (len(abi[2]),len(abi[3])) == ((7,7) if measured['native'].endswith('DispatchV2') else (18,1))
