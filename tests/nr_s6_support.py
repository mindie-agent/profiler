"""Shared fixtures and parsers for the NR-S6 adversarial contracts.

[Role]
  Build captured rows, execute generated scripts in memory, provide a minimal
  torch stub for metadata-install tests, parse pinned C signatures and construct
  the emitted probe namespace.

[Invariants]
  * No fixture derives a signature from the catalog under test.
  * The fake torch stub never touches hardware.

[Timeouts & Locks]
  Pure in-memory helpers.

[Side-Effect Policy]
  No I/O; callers own temporary paths.
"""

from __future__ import annotations

import inspect
import re
import types
from pathlib import Path

from mindie_profiler.fabric_probe import (
    build_fabric_probe_plan, emit_fabric_probe_script,
)
from mindie_profiler.op_api_registry import bind_captured_occurrence
from mindie_profiler.repro_op import _compact_occurrence


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


def qli_row(**overrides):
    row = {
        "op_type": "QuantLightningIndexer", "cann_version": "9.0",
        "input_shapes": ["[48,4,128]", "[48,1,128]", "[48,4]", "[48,4]", "[48,1]",
                         "[1]", "[1]"],
        "input_names": ["query", "key", "weights", "query_dequant_scale",
                        "key_dequant_scale", "actual_seq_lengths_query",
                        "actual_seq_lengths_key"],
        "input_dtypes": ["INT8", "INT8", "FP16", "FP32", "FP32", "INT32", "INT32"],
        "input_formats": ["ND"] * 7,
        "output_shapes": ["[48,4,2048]"], "output_dtypes": ["INT32"],
        "output_formats": ["ND"],
        "attrs": {"query_quant_mode": 0, "key_quant_mode": 0,
                  "layout_query": "TND", "layout_key": "TND",
                  "sparse_count": 2048, "sparse_mode": 3,
                  "pre_tokens": 2147483647, "next_tokens": 2147483647,
                  "actual_seq_lengths_query": [33],
                  "actual_seq_lengths_key": [33]},
    }
    row.update(overrides)
    return row


def exec_script(script: str) -> dict:
    namespace = {"__name__": "nr_s6_generated"}
    exec(compile(script, "<generated>", "exec"), namespace)
    return namespace


def _fake_torch():
    class FakeTensor:
        def __init__(self, values=(), shape=None, dtype=None, device=None):
            self.values = list(values)
            self.shape = tuple(shape if shape is not None else (len(self.values),))
            self.dtype = dtype
            self.device = device

        def numel(self):
            total = 1
            for dim in self.shape:
                total *= dim
            return total

        def copy_(self, other):
            self.values = list(other.values)
            return self

        def reshape(self, shape):
            return FakeTensor(self.values, shape=shape, dtype=self.dtype,
                              device=self.device)

    def tensor(values=(), shape=None, dtype=None, device=None):
        return FakeTensor(values, shape=shape, dtype=dtype, device=device)

    return types.SimpleNamespace(tensor=tensor)




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


def probe_namespace() -> dict:
    plan = build_fabric_probe_plan(world_size=16, duration_s=60)
    script = emit_fabric_probe_script(plan)["script"]
    namespace = {"__name__": "probe_test"}
    exec(compile(script, "<probe>", "exec"), namespace)
    return namespace


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
    return bind_captured_occurrence(row)


def _signature_stub(signature):
    params = []
    for name in signature["positional"]:
        params.append(inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    for name, spec in signature["params"].items():
        if name in signature["positional"]:
            continue
        params.append(inspect.Parameter(
            name, inspect.Parameter.KEYWORD_ONLY,
            default=inspect.Parameter.empty if spec.get("required") else None))
    return inspect.Signature(params)


def spec_is_present(spec):
    if spec.get("kind") == "const":
        return True
    if spec.get("optional") and spec.get("kind") in {"attr", "array"}:
        return spec.get("value") is not None
    return True


def assert_plan_matches_signature(binding, recipe):
    occurrence = _compact_occurrence(binding)
    plan = occurrence["call_plan"]
    signature = recipe["signature"]
    stub = _signature_stub(signature)
    args = [object() for _ in plan["positional"]]
    kwargs = {name: object() for name in plan["keyword"]
              if spec_is_present(plan["keyword"][name])}
    stub.bind(*args, **kwargs)
    assert all(name in signature["params"] for name in plan["keyword"])
    for name in plan["positional_names"]:
        assert name in signature["params"]
    for name, spec in plan["keyword"].items():
        declared = signature["params"][name]["kind"]
        if declared == "tensor_list":
            assert spec["kind"] == "tensor_list", name
        if declared == "tensor" and spec["kind"] == "tensor":
            assert spec.get("list_index") is None or spec.get("list_index") == 0




from collections.abc import Mapping


class KeyMapping(Mapping):
    """Expose keys without hashing them when the mapping is constructed."""

    def __init__(self, key, value=None, prefix=None, callback=None):
        self.key, self.value = key, value
        self.prefix = {} if prefix is None else prefix
        self.callback = callback
        self.reads = 0

    def __len__(self):
        return len(self.prefix) + 1

    def __iter__(self):
        yield from self.prefix
        yield self.key

    def __getitem__(self, key):
        self.reads += 1
        if self.callback is not None:
            self.callback()
        if key is self.key:
            return self.value
        if type(key) is str and key in self.prefix:
            return self.prefix[key]
        if key == self.key:
            return self.value
        raise KeyError(key)


def key_fixture(kind):
    """Return an unsupported key and observable hash/equality counters."""
    calls = {"hash": 0, "eq": 0}

    class CountedInt(int):
        def __hash__(self):
            calls["hash"] += 1
            return int.__hash__(self)

    class CustomString(str):
        def __hash__(self):
            calls["hash"] += 1
            raise AssertionError("unsupported key hash was reached")

        def __eq__(self, other):
            calls["eq"] += 1
            raise AssertionError("unsupported key equality was reached")

    if kind in ("counted", "billion"):
        key = CountedInt(7) if kind == "counted" else "leaf"
        for _ in range(3):
            key = (key,) * (101 if kind == "counted" else 1000)
    elif kind == "frozenset":
        key = frozenset((tuple(range(1000)),))
        for _ in range(3):
            key = frozenset((key,))
    else:
        key = {"list": [1], "dict": {"leaf": 1}, "int": 1,
               "tuple": (1,), "str_subclass": CustomString("field")}[kind]
    return key, calls


def key_timeout_callback(method, sentinel):
    """Reach a key callback through an accepted string-key mapping lookup."""
    class CallbackKey:
        def __hash__(self):
            if method == "hash":
                raise sentinel
            return 0

        def __eq__(self, other):
            raise sentinel

    key = CallbackKey()
    if method == "hash":
        return lambda: {key: None}
    data = {key: None}
    return lambda: data[CallbackKey()]
