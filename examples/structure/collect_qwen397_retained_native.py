"""Reuse the accepted-window native collector for two Q397 captures.

[Role] Fill complete ABI populations where earlier evidence kept examples only.
[Invariants] Accepted Body endpoints and primary geometry are immutable; neither
  native elapsed sums nor graph metadata create new Forward boundaries.
[Timeouts & Locks] One existing local source per process; bounded collector budget.
[Side-Effect Policy] Write new native evidence only; no device or model costs.
"""
import argparse
from pathlib import Path

from collect_glm78_retained_native import extract
from build_qwen_a3_service_cases import read

HERE = Path(__file__).resolve().parent
OUT = HERE / 'acceptance-20261030-highconc-service-refinement/qwen397-a3'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--manifest', type=Path, default=OUT / 'retained-native-cases.json')
    parser.add_argument('--output-dir', type=Path, default=OUT / 'native-partitions')
    args = parser.parse_args()
    manifest = read(args.manifest)
    extract(next(r for r in manifest['cases'] if r['case_id'] == args.case_id),
            output_dir=args.output_dir)
