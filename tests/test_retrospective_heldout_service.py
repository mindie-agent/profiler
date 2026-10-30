"""Small, source-pinned training means exercise the two-variable fit."""
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim", reason="companion Sim acceptance tools require the optional runtime")

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from retrospective_heldout_service import affine_nonnegative


def test_complete_native_training_means_reproduce_frozen_nonnegative_functions():
    fixture=json.loads((ROOT/'tests/fixtures/retrospective_heldout/training.json').read_text())
    for domain in fixture['models']:
        fitted=affine_nonnegative(domain['points'])
        assert len(set(domain['source_shas']))==3
        assert fitted['fixed_us']==pytest.approx(domain['expected']['fixed_us'])
        assert fitted['us_per_axis_unit']==pytest.approx(domain['expected']['us_per_axis_unit'])
        assert fitted['training_sse_us2']==pytest.approx(domain['expected']['training_sse_us2'])


def test_equal_source_weight_is_independent_of_training_call_replication():
    fixture=json.loads((ROOT/'tests/fixtures/retrospective_heldout/training.json').read_text())
    points=fixture['models'][0]['points']
    fitted=affine_nonnegative(points)
    # Replicating every source does not alter the fitted physical function.
    duplicated=affine_nonnegative(points*2)
    assert duplicated['fixed_us']==pytest.approx(fitted['fixed_us'])
    assert duplicated['us_per_axis_unit']==pytest.approx(fitted['us_per_axis_unit'])
    assert duplicated['training_sse_us2']==pytest.approx(fitted['training_sse_us2']*2)
