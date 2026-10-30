"""[Role] Isolate runtime and declared native fusion changes in two A3 cases.
[Invariants] Reuse accepted Body populations; no response is fitted to Body error.
[Timeouts & Locks] Bounded local metadata and existing ten-second Git query.
[Side-Effect Policy] Write local replay manifests and two explicit source cases.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from prepare_decode_runtime_replay import identity, prepare, read

OUT = Path(__file__).resolve().parent
FIXED = Path('/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029')
REVISION = 'a961c114'
IDS = ['glm53flash-a3-tp16-c4-livepre', 'glm53flash-a3-tp16-c16-livepre']


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    base_input = ROOT / 'examples/structure/acceptance-20261030-runtime40e4300e/decode-forward-glm-controller-cases.json'
    base = prepare([base_input], FIXED, REVISION, 'livepre-runtime-a961c114', selected=IDS)
    # Preserve the last explicit c4 communication response. The c16 source had
    # no service responses; this baseline changes only its selected runtime.
    latest_input = ROOT / 'examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-a3-service-cases.json'
    latest_c4 = next(row for row in read(latest_input)['cases'] if row['case_id'] == IDS[0])
    for row in base['cases']:
        if row['case_id'] == IDS[0]:
            row.update(deepcopy(latest_c4))
        row['variant_id'] = base['variant_id']
        row['runtime_refresh'] = {'prior_input_manifest': identity(latest_input if row['case_id'] == IDS[0] else base_input),
                                  'retained_extraction_bytes_unchanged': True,
                                  'scope': 'runtime_only; existing case and response parameters unchanged'}
        assert identity(row['extraction_path'])['sha256'] == row['replay_input_pins']['extraction']['sha256']
        assert identity(row['sim_case_path'])['sha256'] == row['replay_input_pins']['case']['sha256']
    write(OUT / 'decode-forward-baseline-cases.json', base)

    native = deepcopy(base)
    native['variant_id'] = 'livepre-a3-native-fusion-a961c114'
    profiles = {'hc_pre': 'hc_pre_m_k_split_175ef4d4',
                'hc_post': 'hc_post_d_split_175ef4d4',
                'grouped_gate_up_activation_quant': 'grouped_swiglu_quant_int8_split_workspace_ae923905'}
    for row in native['cases']:
        source = Path(row['sim_case_path'])
        case = read(source)
        case['runtime']['kernels'].setdefault('lowerings', {})['native_fusion'] = {
            'implementation': 'declared_native_fusion',
            'options': {'roles': list(profiles), 'traffic_profile': profiles}}
        case['runtime'].setdefault('metadata', {})['native_fusion_source_condition'] = {
            'basis': 'A3 native HC and fused INT8 grouped gate-up observed boundaries',
            'source_case': identity(source), 'capture_binary_identity_established': False,
            'group_list_contents_observed': False, 'new_service_response_parameters': 0}
        destination = OUT / 'cases' / (row['case_id'] + '-native.json')
        write(destination, case)
        row.update(sim_case_path=str(destination), model_declaration=identity(destination), variant_id=native['variant_id'])
        row['replay_input_pins']['case'] = identity(destination)
        row['runtime_refresh']['scope'] = 'explicit A3 native HC and grouped gate-up fusion; same response parameters'
    write(OUT / 'decode-forward-native-cases.json', native)


if __name__ == '__main__':
    main()
