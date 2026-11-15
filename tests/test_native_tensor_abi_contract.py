"""Ordered native-contract adapter tests.

[Role] Prove that a retained ``native_tensor_abi`` cohort contract reaches the
  one canonical slot qualification instead of being dropped as descriptive.
[Invariants] Only the native_tensor_abi kind is promoted; family workload
  contracts stay non-ABI.  Explicit undefined slots remain present.
[Timeouts & Locks] Pure in-memory work.
[Side-Effect Policy] No I/O or global mutation.
"""
from __future__ import annotations

from mindie_profiler.native_tensor_abi import (
    native_abi_from_contract, native_abi_identity,
)


def test_native_contract_emits_complete_ordered_abi():
    contract = ["native_tensor_abi", "AddRmsNormBias", [
        [[256, 4096], "bf16", "ND"],
        [[256, 4096], "bf16", "ND"],
        [[4096], "bf16", "ND"],
        [[], None, None],
    ], [
        [[256, 4096], "bf16", "ND"],
        [[256, 1], "fp32", "ND"],
        [[256, 4096], "bf16", "ND"],
    ]]
    abi = native_abi_from_contract(contract)
    assert abi["status"] == "complete" and abi["verified"] is True
    assert abi["slot_count"] == {"inputs": 4, "outputs": 3}
    assert abi["inputs"][3]["quality"] == "undefined"
    identity = native_abi_identity(abi)
    assert identity["native_operator"] == "AddRmsNormBias"
    assert identity["native_abi_sha256"] == abi["digest"]


def test_family_workload_contract_is_not_promoted_to_native_abi():
    assert native_abi_from_contract(
        ["grouped_matrix", [288, 64, 4096, 256], "fp8_e4m3", "fp8_e4m3",
         "bf16", [64, 4, 2], "fp8_e8m0"]) is None
    assert native_abi_from_contract(
        ["slice_copy", [96, 3336], [96, 3072], "bf16", "bf16"]) is None
    assert native_abi_from_contract(["native_tensor_abi", "", [], []]) is None


def test_incomplete_native_contract_retains_the_gap():
    abi = native_abi_from_contract(
        ["native_tensor_abi", "DynamicQuant",
         [[[32, 7168], "bf16", "ND"]], [[[32], None, "ND"]]])
    assert abi["status"] == "incomplete" and abi["digest"] is None
    assert abi["slot_count"] == {"inputs": 1, "outputs": 1}
    assert any(issue["reason"] == "missing_dtype" for issue in abi["issues"])
