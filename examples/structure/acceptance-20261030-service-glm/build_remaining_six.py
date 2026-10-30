"""Complete one source-selected HC/QKV service domain across all nine captures.

[Role] Prepare the six sources not yet executed with the atomic HC provider.
[Invariants] Reuse the same selectors and per-source native means irrespective of
  previous Body pass; preserve the completed three-source arm and its identities.
[Timeouts & Locks] One bounded source graph at a time, no capture I/O or locks.
[Side-Effect Policy] Writes only third-pass-remaining-six preparation artifacts.
"""
from copy import deepcopy

import build_second_pass
import build_third_pass
from build_service_cases import HERE, ORDER, read, write, pin

DEST = HERE / 'third-pass-remaining-six'
HIGH = ORDER[:3]
REMAINING = [cid for cid in ORDER if cid not in build_third_pass.ORDER]


def main():
    preparation = DEST / 'prepared-prior-nine'
    build_second_pass.main(output_dir=preparation, case_ids=HIGH,
                           variant_id='prepared-native-nine-3b72ea2d-no-prediction')
    previous = read(HERE / 'second-pass/decode-forward-service-cases.json')
    prepared = read(preparation / 'decode-forward-service-cases.json')
    entries = {r['case_id']: r for r in previous['cases'] + prepared['cases']}
    selected = deepcopy(previous)
    selected.update(cases=[entries[cid] for cid in REMAINING],
                    variant_id='prepared-native-nine-for-hc-domain-completion',
                    preparation_sources=[pin(HERE / 'second-pass/decode-forward-service-cases.json'),
                                         pin(preparation / 'decode-forward-service-cases.json')])
    input_path = DEST / 'prepared-prior-cases.json'
    write(input_path, selected)
    build_third_pass.main(manifest_path=input_path, output_dir=DEST, case_ids=REMAINING)
    write(DEST / 'domain-completion.json', {
        'schema_version': 'mindie-native-service-domain-completion/1',
        'selection_basis': 'all nine captures with the same supported premix-absent HC4 BF16 source contract; independent of prior pass status',
        'supported_source_domain': {'tokens_min': 4, 'tokens_max': 256, 'hidden': 4096, 'hc': 4},
        'previous_three_replay_identity': pin(HERE / 'third-pass/decode-forward-service-replay.json'),
        'previous_three_case_ids': build_third_pass.ORDER,
        'remaining_six_case_ids': REMAINING,
        'new_high_three_nine_rule_population_identity': pin(preparation / 'observed-populations.json'),
        'generator_identity': pin(__file__), 'raw_scans': 0, 'new_costs': 0})


if __name__ == '__main__':
    main()
