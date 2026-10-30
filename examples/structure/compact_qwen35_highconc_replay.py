"""Reference repeated declarations without changing saved prediction evidence.

[Role] Stream a previously executed replay into a compact review artifact.
[Invariants] Only repeated calibration declarations become hash-pinned pointers;
  observations, inputs, predictions and parameter query results stay identical.
[Timeouts & Locks] Bounded single-row JSON processing; no subprocess or locks.
[Side-Effect Policy] Write a separate projection and receipt; preserve original.
"""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import ijson
from ijson.common import ObjectBuilder

BASE = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement/qwen35-a5'


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def compact(source, target):
    header = ObjectBuilder()
    with source.open('rb') as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if prefix == 'cases' or prefix.startswith('cases.') or (
                    prefix == '' and event == 'map_key' and value == 'cases'):
                continue
            header.event(event, value)
    rows, projections = [], []
    with source.open('rb') as stream:
        for row in ijson.items(stream, 'cases.item', use_float=True):
            cal = row['calibration_evidence']
            unchanged_before = sha256(canonical({k: v for k, v in row.items() if k != 'calibration_evidence'})).hexdigest()
            for field, pointer in [('prior_evidence', '/runtime/metadata/calibration_evidence/prior_evidence'),
                                   ('declared_service_regimes', '/runtime/kernels/service_regimes')]:
                if field not in cal:
                    continue
                original = cal.pop(field)
                case_pin = row['model_structure_identity']
                case_path = Path(case_pin['path'])
                if digest(case_path) != case_pin['sha256']:
                    raise ValueError('executed_case_changed')
                saved = json.loads(case_path.read_text())
                for part in pointer.strip('/').split('/'):
                    saved = saved[part]
                if saved != original:
                    raise ValueError('referenced_declaration_differs')
                reference = {'case_identity': case_pin, 'json_pointer': pointer,
                             'content_sha256': sha256(canonical(original)).hexdigest()}
                cal[field + '_reference'] = reference
                projections.append({'case_id': row['case_id'], 'field': field, **reference})
            after = sha256(canonical({k: v for k, v in row.items() if k != 'calibration_evidence'})).hexdigest()
            if after != unchanged_before:
                raise ValueError('non_metadata_projection_changed')
            rows.append(row)
    report = header.value
    report['cases'] = rows
    report['format_projection'] = {'original_report_identity': {'path': str(source.resolve()), 'sha256': digest(source)},
        'original_size_bytes': source.stat().st_size, 'changed_fields': ['calibration_evidence.prior_evidence',
        'calibration_evidence.declared_service_regimes'], 'observations_predictions_parameters_unchanged': True,
        'new_cost_predictions': 0, 'new_raw_scans': 0}
    target.write_text(json.dumps(report, indent=2) + '\n')
    receipt = {'schema_version': 'mindie-replay-format-projection/1', **report['format_projection'],
        'projected_report_identity': {'path': str(target.resolve()), 'sha256': digest(target)},
        'projected_size_bytes': target.stat().st_size, 'verified_references': projections,
        'case_rows': len(rows), 'producer_identity': {'path': str(Path(__file__).resolve()), 'sha256': digest(__file__)}}
    (target.parent / 'format-projection.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'path': str(target), 'sha256': digest(target), 'bytes': target.stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=BASE)
    args = parser.parse_args()
    compact(args.directory / 'decode-forward-replay.json', args.directory / 'decode-forward-replay.compact.json')
