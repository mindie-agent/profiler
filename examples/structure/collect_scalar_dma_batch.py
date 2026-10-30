"""Run one bounded retained-window PMU pass for six declared local sources.

[Role] Pin inputs, preserve completed extraction reuse and record exact attempts.
[Invariants] No prediction/device calls; one new CSV pass per source at most.
[Timeouts & Locks] Sequential child workers, each 190s around a 180s scan budget.
[Side-Effect Policy] Writes only scalar-dma-* evidence and its batch receipt.
"""
import json
from pathlib import Path
import subprocess
import sys

from collect_scalar_dma_pmu import identity, read

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/observations/sources/arch3510-physical-services'


def main():
    script = Path(__file__).with_name('collect_scalar_dma_pmu.py')
    glm = read(ROOT / 'examples/structure/acceptance-20261030-service-glm/observed-populations.json')
    selected = {'glm53flash-a5-tp8-c1', 'a5_glm53flash_tp8_c8_p4k', 'a5_glm53flash_tp8_c4_p8k'}
    actuals = [Path(r['groups'][0]['actual_identity']['path']) for r in glm['cases'] if r['case_id'] in selected]
    hardware = {r['case_id']: r['case_identity'] for r in glm['cases']}
    folder = ROOT / 'examples/structure/acceptance-20261030-qwen-source-native-operators/retained-six-actual'
    actuals.extend(folder / f'body-operator-qwen35-35b-a5-tp4-c{c}-graph-qwen-source-gdn-native.actual.json'
                   for c in (4, 64, 128))
    results = []
    DEST.mkdir(parents=True, exist_ok=True)
    for path in actuals:
        actual = read(path)
        cid = actual['source_case_id']
        output = DEST / f'scalar-dma-{cid}.json'
        reused = output.exists()
        if reused:
            saved = read(output)
            if (saved['actual_identity'] != identity(path) or
                    not saved['complete_native_histograms_match_actual'] or
                    saved['source_identity']['sha256'] != actual['source_identity']['sha256']):
                raise ValueError(f'existing_scalar_dma_evidence_identity_differs:{cid}')
        else:
            hardware_pin = hardware.get(cid, actual['case_identity'])
            if identity(hardware_pin['path']) != hardware_pin:
                raise ValueError(f'hardware_declaration_changed:{cid}')
            result = subprocess.run([sys.executable, str(script), '--actual', str(path), '--output', str(output),
                                     '--hardware-case', hardware_pin['path']],
                                    text=True, capture_output=True, timeout=190, cwd=ROOT)
            log = DEST / f'scalar-dma-{cid}.run.log'
            log.write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f'scalar_dma_extraction_failed:{cid}:see {log}')
            saved = read(output)
        results.append({'case_id': cid, 'output_identity': identity(output), 'actual_identity': identity(path),
                        'source_identity': saved['source_identity'], 'forward_count': saved['forward_count'],
                        'native_counts': saved['native_counts'], 'execution': saved['execution'],
                        'executed_extractor_identity': saved['extractor_identity'],
                        'reused_completed_extraction': reused})
        print(cid, 'retained' if reused else 'new', saved['native_counts'], flush=True)
    receipt = {'schema_version': 'mindie-scalar-dma-native-pmu-batch/1', 'status': 'completed',
               'cases': results, 'extractor_identity': identity(script), 'batch_identity': identity(__file__),
               'new_source_passes': sum(not r['reused_completed_extraction'] for r in results),
               'retained_source_passes': sum(r['reused_completed_extraction'] for r in results),
               'new_predictions': 0, 'new_device_collections': 0,
               'forward_count': sum(r['forward_count'] for r in results),
               'peak_rss_bytes': max(r['execution']['peak_rss_bytes'] for r in results)}
    receipt['preflight_attempt'] = {'case_id': 'a5_glm53flash_tp8_c8_p4k',
        'status': 'failed_before_csv_scan', 'reason': 'Historical mutable checkout case bytes differ; hardware SKU now has a separate pinned same-source service-case declaration.',
        'log_identity': identity(DEST / 'scalar-dma-initial-hardware-preflight.run.log'),
        'failed_source_passes': 0}
    (DEST / 'scalar-dma-extraction-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
