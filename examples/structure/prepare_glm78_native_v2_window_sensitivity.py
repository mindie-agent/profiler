"""Declare the preselected window-8 sensitivity against the window-16 caller.

[Role] Change only declared peer concurrency, retaining all observed responses.
[Invariants] Neither window is identified from the capture. No accuracy result
  selects this value, and neither arm's original evidence is overwritten.
[Timeouts & Locks] Small retained inputs; no raw scan, cost, locks or devices.
[Side-Effect Policy] Write independent sensitivity cases and manifest only.
"""
from copy import deepcopy
from pathlib import Path

from build_qwen_a3_service_cases import identity, read, write


HERE = Path(__file__).resolve().parent
BASE = HERE / 'acceptance-20261030-glm78-native-v2-service'
OUT = BASE / 'window8-sensitivity'


def main():
    manifest_path = BASE / 'decode-forward-glm78-native-v2-cases.json'
    manifest = read(manifest_path)
    for row in manifest['cases']:
        source = row['sim_case_path']; case = read(source)
        protocol = case['runtime']['kernels']['native_moe_protocol']
        if protocol['max_inflight_per_rank'] != 16: raise ValueError('baseline_window_not_16')
        protocol['max_inflight_per_rank'] = 8
        assumption = case['metadata']['native_v2_caller_assumption']
        assumption.update(max_inflight_per_rank=8,
            basis='predeclared_half_EP_logical_peer_window_sensitivity',
            selection_basis='chosen_before_cost_as_8_vs_16_sensitivity; no_error_based_selection')
        for rule in case['runtime']['kernels']['service_regimes']:
            provenance = rule.get('provenance', {})
            if 'transport_assumption' in provenance:
                provenance['transport_assumption'] = deepcopy(assumption)
        path = OUT / 'cases' / (row['case_id'] + '-window8.json'); write(path,case)
        row.update(sim_case_path=str(path), model_declaration=identity(path),
                   variant_id='glm78-native-v2-window8-sensitivity')
        row['replay_input_pins']['case'] = identity(path)
        row['scenario_evidence']['native_v2_transport_assumption'] = deepcopy(assumption)
        row['scenario_evidence']['window16_case_identity'] = identity(source)
    manifest['baseline_identity'] = identity(manifest_path)
    manifest['variant_id'] = 'glm78-native-v2-window8-sensitivity'
    manifest['selection_policy'] = 'window16 remains the declared primary arm; window8 is an independently retained sensitivity, not a best-error selector'
    write(OUT / 'decode-forward-glm78-native-v2-window8-cases.json',manifest)


if __name__ == '__main__': main()
