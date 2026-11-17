"""Retained captured-row and public ABI bindings for keeper tests.

[Role]
  Build captured operator rows, pinned C signature parsers and the public
  occurrence bindings that the retained mapping suites exercise.
[Invariants]
  No fixture derives a signature from the catalog under test; explicit slot
  names, dtypes and layouts are declared by the fixture only.
[Timeouts & Locks]
  Pure in-memory helpers.
[Side-Effect Policy]
  No I/O; callers own temporary paths.
"""

from __future__ import annotations

import re
from pathlib import Path

from mindie_profiler.op_api_registry import bind_captured_occurrence


def fa_row(**overrides):
    row = {
        "op_type": "aclnnFlashAttentionVarLenScore", "cann_version": "8.0",
        "input_shapes": ["[48,8,128]"] * 7, "input_dtypes": ["BF16"] * 7,
        "input_formats": ["ND"] * 7,
        "output_shapes": ["[48,8,128]"] + ["[48,8,8]"] * 3,
        "output_dtypes": ["BF16"] * 4, "output_formats": ["ND"] * 4,
        "attrs": {"input_layout": "TND", "num_heads": 8, "scale": 0.088,
                  "keep_prob": 1.0, "pre_tokens": 2147483647, "next_tokens": 0,
                  "inner_precise": 1, "sparse_mode": 3,
                  "actual_seq_q_len": [33], "actual_seq_kv_len": [33]},
    }
    row.update(overrides)
    return row


def paged_row(**overrides):
    row = {
        "op_type": "aclnnPagedAttention", "cann_version": "8.0",
        "input_shapes": ["[16,8,128]", "[256,16,8,128]", "[256,16,8,128]",
                         "[16,16]", "[16]"],
        "input_names": ["query", "key_cache", "value_cache", "block_table",
                        "context_lens"],
        "input_dtypes": ["BF16", "BF16", "BF16", "INT32", "INT32"],
        "input_formats": ["ND"] * 5,
        "output_shapes": ["[16,8,128]"], "output_names": ["out"],
        "output_dtypes": ["BF16"], "output_formats": ["ND"],
        "attrs": {"num_kv_heads": 8, "num_heads": 8, "scale_value": 0.088,
                  "kv_len": 2048},
    }
    row.update(overrides)
    return row


def fa_binding():
    row = {
        "op_type": "aclnnFlashAttentionVarLenScore", "cann_version": "8.0",
        "input_shapes": ["[48,8,128]"] * 7, "input_dtypes": ["BF16"] * 7,
        "input_formats": ["ND"] * 7,
        "output_shapes": ["[48,8,128]"] + ["[48,8,8]"] * 3,
        "output_dtypes": ["BF16"] * 4, "output_formats": ["ND"] * 4,
        "attrs": {"input_layout": "TND", "num_heads": 8, "scale": 0.088,
                  "keep_prob": 1.0, "pre_tokens": 2147483647, "next_tokens": 0,
                  "inner_precise": 1, "sparse_mode": 3,
                  "actual_seq_q_len": [33], "actual_seq_kv_len": [33]},
    }
    return bind_captured_occurrence(row)


def gmm_binding():
    row = {
        "op_type": "aclnnGroupedMatmulV4", "cann_version": "9.0",
        "input_shapes": ["[64,128]", "[4,128,64]", "[4]"],
        "input_names": ["x", "weight", "group_list"],
        "input_dtypes": ["BF16", "BF16", "INT64"],
        "input_formats": ["ND", "FRACTAL_NZ", "ND"],
        "output_shapes": ["[64,64]"], "output_names": ["out"],
        "output_dtypes": ["BF16"], "output_formats": ["ND"],
        "attrs": {"group_list_type": 0, "group_type": 0, "act_type": 0,
                  "split_item": 0, "group_list": [16, 32, 48, 64]},
    }
    return bind_captured_occurrence(row)


def paged_binding():
    return bind_captured_occurrence(paged_row())


def _parse_header_signature(path: Path, symbol: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\b" + re.escape(symbol) + r"\s*\(", text)
    assert match, symbol
    index, depth = match.end(), 1
    while depth:
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        index += 1
    body = text[match.end():index - 1]
    parts, depth, current = [], 0, ""
    for char in body:
        if char in "([<":
            depth += 1
        elif char in ")]>":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return [re.split(r"[\s*]+", part.strip())[-1] for part in parts]
