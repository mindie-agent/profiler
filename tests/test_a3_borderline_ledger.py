"""Real retained A3 populations guard conditional/strict and batch boundaries."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'examples/structure'
sys.path.insert(0,str(SCRIPTS))
from diagnose_a3_borderline import family_ledger

BASE=SCRIPTS/'acceptance-20261030-a3-borderline'


def load_case(arm):
    score=json.loads((BASE/f'{arm}-30d/body-operator-family-scoreboard.json').read_text())
    return json.loads(Path(score['cases'][0]['case_detail_identity']['path']).read_text())['cases'][0]


def test_kimi_full_batch_reference_supersedes_incomplete_single_sequence():
    case=load_case('kimi')
    references=json.loads((BASE/'kimi-complete-native-references.json').read_text())['groups']
    fia=next(g for g in references if g['native_operator_type']=='FusedInferAttentionScore')
    assert fia['observed_us']['count']==220
    assert len({p['op_id'] for p in fia['declared_programs']})==32
    assert fia['source_correspondence']['observed_physical_heads']==16
    assert fia['source_correspondence']['declared_logical_heads']==12
    result=family_ledger(case,references)
    rows=[r for r in result['priced_rows'] if r['native_operator_type']=='FusedInferAttentionScore']
    assert len(rows)==1
    assert rows[0]['sim_mean_us']==pytest.approx(160)
    assert not rows[0]['strict_accuracy_implied']
    assert len(result['superseded_references'])==1
    assert rows[0]['signed_activity_residual_ms_per_forward']==pytest.approx(-.11758555)


def test_wrapper_requires_typed_confirmation_and_never_changes_body_budget():
    case=load_case('kimi')
    original=family_ledger(case)
    assert not original['controller_overlays']
    assert any(r['native_operator_type']=='reduce_scatterAicpuKernel' for r in original['unpriced_families'])
    classified=family_ledger(case,confirmed_controller_types=['reduce_scatterAicpuKernel'])
    overlay=classified['controller_overlays'][0]
    assert overlay['observed_us']['count']==1760
    assert overlay['activity_ms_per_forward']==pytest.approx(1.3755345454545453)
    assert overlay['body_span_modified'] is False
    assert not any(r['native_operator_type']=='reduce_scatterAicpuKernel' for r in classified['priced_rows'])


def test_v4_same_population_distinguishes_unpriced_activity_from_error():
    case=load_case('v4');result=family_ledger(case)
    assert case['forward_count']==104
    expert=next(r for r in result['priced_rows'] if r['native_operator_type']=='GroupedMatmul')
    assert expert['event_count']==43*104
    assert expert['calls_per_forward']==43
    assert expert['evidence_strength']=='conditional_source_reference'
    assert expert['signed_activity_residual_ms_per_forward']==pytest.approx(-.5049882892996864)
    compressor=next(r for r in result['unpriced_families'] if r['native_operator_type']=='Compressor')
    assert compressor['event_count']==6448
    assert compressor['unpriced_activity_ms_per_forward']>3
    assert compressor['sim_mean_us'] is None
    assert compressor['signed_activity_residual_ms_per_forward'] is None
    assert len(result['top3_underestimates'])==3
