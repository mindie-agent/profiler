"""Real routing design points must not imply independent primitive prices."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from join_routing_source_inventory import count_features,matrix_rank


def fixture():
    return json.loads((ROOT/'tests/fixtures/scalar_dma/routing_source_design.json').read_text())


def test_real_routing_source_counts_are_rank_deficient():
    evidence=fixture();matrix=[]
    for record in evidence['records']:
        geometry=record['conditional_source_geometry']
        features=count_features(geometry['assignments'],geometry['active_owners'],geometry['experts'])
        assert features==record['count_features']
        assert features['count_gm_load32_all_owners']==4*geometry['assignments']-2*geometry['active_owners']
        assert record['calls']==42*record['forward_count']
        matrix.append([features[name] for name in evidence['design']['feature_names']])
    assert matrix_rank(matrix)==3
    assert len(matrix[0])-matrix_rank(matrix)==10


def test_repeated_kernel_calls_do_not_add_an_independent_physical_design_point():
    evidence=fixture();matrix=evidence['design']['feature_matrix']
    # More calls tighten the same observed mean; they cannot untangle source
    # features which co-vary at every retained geometry.
    assert matrix_rank(matrix*42)==matrix_rank(matrix)
    names=evidence['design']['feature_names']
    fixed=[names.index(name) for name in ('intercept','owner0_ub_getvalue','owner0_scalar_add',
                                        'owner0_ub_setvalue','owner0_pipe_v_barrier')]
    assert matrix_rank([[row[i] for i in fixed] for row in matrix])==1
