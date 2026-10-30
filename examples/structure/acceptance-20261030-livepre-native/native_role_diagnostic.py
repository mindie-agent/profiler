"""[Role] Inspect source-labelled native roles in two complete A3 Body runs.
[Invariants] Role identities come from Sim metadata; observations never set costs.
  Scheduled intervals include wait and need not sum to the Body span.
[Timeouts & Locks] Two finite local predictions; no raw captures, locks or devices.
[Side-Effect Policy] Write one compact native-role diagnostic beside the cases.
"""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from replay_decode_forwards import _sim_identity
from mindie_sim import predict


def read(path):
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata exceeds bounded read')
    return json.loads(path.read_text())


def pin(path):
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()}


def main():
    started = time.monotonic()
    runtime = _sim_identity()
    rows = []
    for batch in (4, 16):
        case_id = f'glm53flash-a3-tp16-c{batch}-livepre'
        path = HERE / 'cases' / f'{case_id}-native.json'
        case = read(path)
        result = predict(case, scope='body', phase='decode', tokens=6,
                         sequences=batch, context=4096, event_limit=0)
        partitions = read(HERE.parent / 'acceptance-20261030-glm-source-accepted-26' /
                          'additional-native-partitions' / f'{case_id}-native-partitions.json')
        actual_path = Path(partitions['actual_identity']['path'])
        if pin(actual_path)['sha256'] != partitions['actual_identity']['sha256']:
            raise ValueError('retained population changed')
        actual = read(actual_path)
        groups = defaultdict(list)
        for event in result['timeline']:
            role = event.get('fusion_role')
            if (event['family'], event['recipe']) == ('grouped_gemm', 'grouped_down'):
                role = 'expert_down'
            elif (event['family'], event['recipe']) == ('attention', 'latent_attention_batch'):
                role = 'indexed_attention_batch'
            if role:
                groups[role].append(event)
        native_names = {'hc_pre': 'HcPre', 'hc_post': 'HcPost',
                        'grouped_gate_up_activation_quant': 'GroupedMatmulSwigluQuant',
                        'expert_down': 'GroupedMatmul',
                        'indexed_attention_batch': 'KvQuantSparseFlashAttentionVllm'}
        details = []
        for role, events in groups.items():
            native = native_names[role]
            observed = [family for family in actual['families'] if family['native_operator_type'] == native]
            histogram = defaultdict(int)
            for family in observed:
                for ns, count in family['duration_ns_counter']:
                    histogram[int(ns)] += int(count)
            count = sum(histogram.values())
            if not count:
                raise ValueError('complete native family missing: ' + native)
            observed_us = sum(ns*n for ns, n in histogram.items()) / count / 1000
            predicted_us = sum(event['complete_ms']-event['ready_ms'] for event in events)*1000/len(events)
            calls = count / actual['forward_count']
            if calls != len(events):
                raise ValueError('native role multiplicity differs: ' + role)
            details.append({'role': role, 'native_operator_type': native, 'calls_per_forward': calls,
                            'observed_native_mean_us': observed_us, 'scheduled_role_mean_us': predicted_us,
                            'scheduled_minus_observed_activity_ms': (predicted_us-observed_us)*calls/1000,
                            'programs': sorted({str(event.get('physical_source_program') or event['program']) for event in events}),
                            'basis': 'explicit_source_role_service_reference; not strict ABI proof or additive wall attribution'})
        rows.append({'case_id': case_id, 'case_identity': pin(path),
                     'actual_identity': partitions['actual_identity'],
                     'body_forward_ms': result['body_forward_ms'], 'roles': details})
    if runtime != _sim_identity():
        raise ValueError('runtime changed during diagnostic')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output = {'schema_version': 'mindie-native-role-diagnostic/1', 'runtime_identity': runtime,
              'cases': rows, 'execution': {'elapsed_seconds': time.monotonic()-started,
              'peak_rss_bytes': int(rss if sys.platform == 'darwin' else rss*1024), 'raw_reads': 0}}
    (HERE / 'native-role-diagnostic.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
