"""Collect missing low-row GLM78 native evidence within retained Body windows.

[Role] Invoke the existing streaming native collector for three retained sources.
[Invariants] Original Forward endpoints, source identity and geometry are fixed;
  no source window is created and no observed timing is inferred from prediction.
[Timeouts & Locks] One source at a time with the collector's 180s bounded budget.
[Side-Effect Policy] Local capture reads and owned evidence only; no devices.
"""
from pathlib import Path

from build_qwen_a3_service_cases import read
from collect_glm78_retained_native import extract


HERE=Path(__file__).resolve().parent
BASE=HERE/'acceptance-20261030-a3-tail-service-refinement'


if __name__=='__main__':
    for row in read(BASE/'glm78-tp-join/decode-forward-tp-join-cases.json')['cases']:
        extract(row,output_dir=BASE/'glm78-low-native')
