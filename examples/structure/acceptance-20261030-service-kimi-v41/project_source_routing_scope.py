"""Correct source-rank display without executing or modifying saved costs.

[Role] Project explicit force-EPLB scope into an already completed replay.
[Invariants] Original worker identities and all numeric predictions are retained.
  New adapter identity describes only this metadata/comparison projection.
[Timeouts & Locks] Bounded local JSON; no workers, locks or runtime imports.
[Side-Effect Policy] Write a separate report, preserving the original cost receipt.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import body_forward_comparison as body
from replay_decode_forwards import render


def pin(path):
    return {'path': str(path.resolve()), 'sha256': sha256(path.read_bytes()).hexdigest()}


def main():
    source = HERE / 'decode-forward-source-routing-84d80b40-replay.json'
    report = json.loads(source.read_text())
    manifest = json.loads((HERE / 'decode-forward-source-routing-84d80b40-cases.json').read_text())
    by_id = {r['case_id']: r for r in manifest['cases']}
    adapter = pin(Path(body.__file__))
    for row in report['cases']:
        path = Path(by_id[row['source_case_id']]['sim_case_path'])
        if pin(path)['sha256'] != row['model_structure_identity']['sha256']:
            raise ValueError('source_case_changed')
        case = json.loads(path.read_text())
        prediction = row['prediction']
        previous_prediction = deepcopy(prediction)
        prediction['source_routing_declaration'] = body.source_routing_declaration(case['runtime']['kernels'])
        compared = body.compare_body_forward(prediction, row['observed'])
        if {k:v for k,v in compared.items() if k != 'assumptions'} != {
                k:v for k,v in row['comparison'].items() if k != 'assumptions'}:
            raise ValueError('comparison_numeric_changed')
        row['comparison']['assumptions'] = compared['assumptions']
        row['per_layer_comparison']['assumptions'] = body.compare_layers(prediction, row['observed'])['assumptions']
        if {k:v for k,v in prediction.items() if k != 'source_routing_declaration'} != previous_prediction:
            raise ValueError('prediction_numeric_changed')
        row['comparison_projection'] = {'adapter_identity': adapter,
            'original_cost_receipt': pin(source), 'new_prediction_executed': False,
            'numeric_prediction_unchanged': True,
            'purpose': 'Explicit source rank-zero compute and asymmetric peer-transport display'}
    report['comparison_projection'] = {'source_receipt': pin(source),
        'adapter_identity': adapter, 'new_predictions': 0, 'raw_event_reads': 0,
        'original_worker_and_runtime_identities_retained': True,
        'numeric_prediction_and_thresholds_unchanged': True}
    target = HERE / 'decode-forward-source-routing-84d80b40-projected.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    target.with_suffix('.md').write_text(render(report))
    print(json.dumps(pin(target)))


if __name__ == '__main__':
    main()
