"""Real retained results exercise generation-complete scoreboard publication."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
import pipeline


def test_interrupted_generation_and_partial_selection_preserve_complete_board(tmp_path, monkeypatch):
    samples = json.loads((ROOT / 'tests/fixtures/prefill/pipeline_projection.json').read_text())['cases']
    rows = [deepcopy(s['row']) for s in samples[:2]]
    manifest = tmp_path / 'cases.json'
    manifest.write_text(json.dumps({'schema_version': 'mindie-cases/1', 'cases': rows}))
    archive = tmp_path / 'archive'
    cards = [pipeline.project(row, sample['result'], pipeline.archive_report(sample['result'], archive))
             for row, sample in zip(rows, samples)]
    output = tmp_path / 'prefill.json'
    previous = {'status': 'completed', 'scope': 'body', 'cases': cards,
                'summary': pipeline.summarize(cards, len(cards))}
    pipeline.publish(previous, output)
    original = (output.read_bytes(), output.with_suffix('.md').read_bytes())
    monkeypatch.setattr(pipeline, '_sim_identity', lambda: {'package_sha256': 'new-generation'})

    with pytest.raises(ValueError, match='partial_selection_cannot_replace_complete_scoreboard'):
        pipeline.run(manifest, output=output, archive_root=archive, case_ids=[rows[0]['id']])

    def interrupted(selected, *args):
        yield selected[0], samples[0]['result']
        assert (output.read_bytes(), output.with_suffix('.md').read_bytes()) == original
        raise KeyboardInterrupt

    monkeypatch.setattr(pipeline, 'execute_rows', interrupted)
    with pytest.raises(KeyboardInterrupt):
        pipeline.run(manifest, output=output, archive_root=archive)
    assert (output.read_bytes(), output.with_suffix('.md').read_bytes()) == original

    def complete(selected, *args):
        for row, sample in zip(selected, samples):
            assert (output.read_bytes(), output.with_suffix('.md').read_bytes()) == original
            yield row, sample['result']

    monkeypatch.setattr(pipeline, 'execute_rows', complete)
    result = pipeline.run(manifest, output=output, archive_root=archive)
    assert result['summary']['sources'] == result['summary']['requested_sources'] == 2
    assert result['status'] == 'completed'
    assert json.loads(output.read_text()) == result
    assert result['runtime']['package_sha256'] == 'new-generation'
    assert [c['comparison'] for c in result['cases']] == [s['result']['comparison'] for s in samples[:2]]
