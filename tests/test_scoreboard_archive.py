"""Actual Decode arithmetic survives compact publication and archived history."""
import importlib
import json
from pathlib import Path

import pytest


def test_real_comparisons_preserved_and_tampered_summary_rejected(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / 'examples/structure'))
    producer = importlib.import_module('priority_decode_scoreboard')
    reviewer = importlib.import_module('review_priority_decode_scoreboard')
    source = root / 'examples/structure/acceptance-20261030-a3-v4-caller-cc245da6/decode-forward-a3-v4-caller-replay.json'
    report = producer.build([source], [])
    out = tmp_path / 'current.json'
    producer.publish(report, out, tmp_path / 'archive')
    compact = json.loads(out.read_text())
    assert compact['summary'] == report['summary']
    assert len(compact['current_body_comparisons']) == len(report['current_body_comparisons'])
    assert 'body_comparisons' not in compact
    assert reviewer.review(out)['status'] == 'passed'
    compact['summary']['current_body_passed'] += 1
    out.write_text(json.dumps(compact))
    result = reviewer.review(out)
    assert result['status'] == 'failed'
    assert 'Compact summary preserves full evidence' in result['failures']
