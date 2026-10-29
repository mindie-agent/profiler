"""Run selected retained body populations through isolated operator workers.

[Role] Apply existing extraction and comparison tools to ordered body manifests.
[Invariants] Use observed query/batch and explicit retained context; no fitting.
  Each source runs in its own process so working sets do not accumulate.
[Timeouts & Locks] Serial workers, 300 s extraction and 900 s final comparison.
[Side-Effect Policy] Read local captures; write reports/logs in the output folder.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--manifest', type=Path, action='append', required=True)
    parser.add_argument('--sim-root', type=Path, required=True)
    parser.add_argument('--case-contains', default='')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join((str(args.sim_root), str(scripts.parents[1])))}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pooled = []
    for manifest_path in args.manifest:
        manifest = json.loads(manifest_path.read_text())
        receipt = manifest_path.with_name('decode-forward-auto-acceptance.json')
        for case in manifest['cases']:
            if args.case_contains not in case['case_id']:
                continue
            original = Path(case['sim_case_path'])
            relative = Path('examples') / str(original).split('/examples/', 1)[1]
            case_dir = (args.sim_root / relative).parent
            command = [sys.executable, str(scripts / 'replay_body_operator_families.py'),
                       '--receipt', str(receipt), '--case-id', case['case_id'],
                       '--case-dir', str(case_dir), '--output-dir', str(args.output_dir),
                       '--geometry-limit', '1', '--context-tokens', str(case['geometry']['context_tokens'])]
            log_path = args.output_dir / (case['case_id'] + '.log')
            with log_path.open('w') as stream:
                subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT,
                               check=True, timeout=300)
            sidecar = json.loads((args.output_dir / 'steady-layer-pooled.json').read_text())
            pooled.extend(sidecar['cases'])
            print(json.dumps({'case_id': case['case_id'], 'status': 'extracted', 'log': str(log_path)}), flush=True)
    (args.output_dir / 'steady-layer-pooled.json').write_text(json.dumps({
        'schema_version': 'mindie-steady-layer-pooled/1', 'cases': pooled,
        'population_basis': 'pooled_layer_calls_excluding_layer0',
        'input_manifests': [{'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()}
                            for path in args.manifest]}, separators=(',', ':')) + '\n')
    with (args.output_dir / 'comparison.log').open('w') as stream:
        subprocess.run([sys.executable, str(scripts / 'compare_body_operator_families.py'),
                        '--output-dir', str(args.output_dir)], env=env, check=True, timeout=900,
                       stdout=stream, stderr=subprocess.STDOUT)
    print(json.dumps({'status': 'compared', 'output_dir': str(args.output_dir)}), flush=True)


if __name__ == '__main__':
    main()
