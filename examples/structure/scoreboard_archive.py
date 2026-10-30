"""[Role] Publish compact scoreboards with content-addressed full evidence.
[Invariants] Projection never selects by error or changes a measured value;
  the complete history remains byte-verifiable in an external archive.
[Timeouts & Locks] Streaming JSON output and hashing; no subprocesses or locks.
[Side-Effect Policy] Write immutable archive objects and small JSON summaries.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    value = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def archive_report(report, root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.scoreboard-', suffix='.json', dir=root)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(report, stream, separators=(',', ':'), allow_nan=False)
            stream.write('\n')
        identity = digest(temporary)
        target = root / (identity + '.json')
        if target.exists():
            if digest(target) != identity:
                raise ValueError('archive content does not match its SHA256 name')
            temporary.unlink()
        else:
            os.replace(temporary, target)
        return {'path': str(target.resolve()), 'sha256': identity,
                'size_bytes': target.stat().st_size, 'format': 'full_scoreboard_json'}
    finally:
        temporary.unlink(missing_ok=True)


BODY_FIELDS = ('model_group', 'case_id', 'variant_id', 'receipt', 'source_identity',
               'runtime_identity', 'geometry', 'comparison', 'error', 'display_status',
               'body_activity_ms', 'body_internal_gap_ms', 'calibration_origin')
COHORT_FIELDS = ('case_id', 'cohort_id', 'receipt', 'geometry', 'source_identity',
                 'native_operator_type', 'declared_role', 'observed_calls', 'observed_us',
                 'predicted_us', 'per_call_diff_us', 'signed_activity_residual_ms_per_forward',
                 'accuracy_pass', 'accuracy_tier', 'status')


def project(report, evidence):
    def rows(key, fields):
        return [{k: row[k] for k in fields if k in row} for row in report.get(key, [])]
    result = {key: report[key] for key in ('schema_version', 'summary', 'inputs',
              'additional_evidence', 'limitations', 'execution', 'input_manifest_identity',
              'priority_focus') if key in report}
    result['publication_format'] = 'mindie-priority-scoreboard-compact/1'
    result['full_evidence'] = evidence
    result['evidence_scope'] = 'Historical arms, per-layer details, contracts and native references are in full_evidence.'
    for key in ('current_body_comparisons', 'latest_body_attempts', 'body_failed_attempts'):
        result[key] = rows(key, BODY_FIELDS)
    result['current_operator_cohorts'] = rows('current_operator_cohorts', COHORT_FIELDS)
    result['archived_row_counts'] = {key: len(value) for key, value in report.items() if isinstance(value, list)}
    return result


def resolve_full(path):
    """Resolve only our small publication wrapper; missing evidence is explicit."""
    path = Path(path)
    if path.stat().st_size > 5_000_000:
        return path
    with path.open() as stream:
        document = json.load(stream)
    if document.get('publication_format') != 'mindie-priority-scoreboard-compact/1':
        return path
    evidence = document['full_evidence']; target = Path(evidence['path'])
    if digest(target) != evidence['sha256'] or target.stat().st_size != evidence['size_bytes']:
        raise ValueError('scoreboard archive identity mismatch')
    return target
