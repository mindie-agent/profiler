"""Pure-data L0 SKU microbench preset emitter targeting ``mindie-bench-plan/2``.

[Role]
  Compile minimal hardware L0 calibration presets (completion minima, GEMM,
  grouped-MoE routing histograms, and host DMA IO) into a sealed
  ``mindie-bench-plan/2`` plan whose execution delegates 100% to
  ``campaign_runner.run_campaign``.  Replaces the retired 647-line monolith.

[Invariants]
  * Pure CPU data emitter (``DEV-ZERO-CTX``): zero ``torch``, ``torch_npu``,
    or ``mindie_sim`` imports, and zero execution/timing logic.
  * Arch-gated dtypes: A2/A3 refuse native FP8; A5 enables FP8/MXFP8/MXFP4/HiF8.
  * ``group_list`` is always an integer list conserving total tokens ``M``.

[Timeouts & Locks]
  Pure in-memory plan construction; no locks, timers, or I/O.

[Side-Effect Policy]
  None; returns fresh plan dicts.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from ..events import ProfilerUsageError
from .campaign_store import (
    PLAN_V2_SCHEMA, canonical_case_id, canonical_key_digest,
    normalize_canonical_key, seal_payload,
)
from .env_fingerprint import infer_soc_arch
from .operators_common import A5_ONLY_FP8_DTYPES, validate_dtype_for_arch
from .profiles import profile_section

_CFG = profile_section("sku_microbench")
_SIG_VER = int(profile_section("campaign")["sig_version"])
DAV_2201 = "DAV_2201"
A2_SKUS = ("Ascend910B1", "Ascend910B2", "Ascend910B2C", "Ascend910B3", "Ascend910B4", "Ascend910B4-1")
A3_SKUS = ("Ascend910_9391", "Ascend910_9392", "Ascend910_9381", "Ascend910_9382", "Ascend910_9372", "Ascend910_9362")
A5_SKUS = ("Ascend950DT_9581", "Ascend950DT_9582", "Ascend950PR_9579", "Ascend950PR_958b")
SUPPORTED_SKUS = (DAV_2201, *A2_SKUS, *A3_SKUS, *A5_SKUS)
BASE_DTYPES = ("bf16", "fp16", "int8", "w4a8")
A5_EXTRA_DTYPES = ("fp8_e4m3", "fp8_e5m2", "mxfp8", "mxfp4", "hif8")
DOMAIN_IDS = tuple(int(k) for k, name in _CFG["domain_names"].items() if name != "attention_state")
_DMA = {**dict.fromkeys(A2_SKUS, "pcie_dma"), **dict.fromkeys(A3_SKUS, "hccs_dma"), **dict.fromkeys(A5_SKUS, "ub_dma")}


def supported_dtypes_for_sku(sku: str) -> tuple[str, ...]:
    """Return arch-gated dtypes supported by ``sku``."""
    return (*BASE_DTYPES, *A5_EXTRA_DTYPES) if infer_soc_arch(sku) == "A5" else BASE_DTYPES


def uniform_counts(experts: int, tokens: int) -> list[int]:
    """Integer uniform routing histogram conserving ``tokens``."""
    if experts < 1 or tokens < 0:
        raise ProfilerUsageError("bench_routing_shape_invalid")
    q, rem = divmod(int(tokens), int(experts))
    return [q + (1 if idx < rem else 0) for idx in range(int(experts))]


def zipf_counts(experts: int, tokens: int, exponent: float | None = None) -> list[int]:
    """Deterministic integer Zipf routing histogram conserving ``tokens``."""
    exp = float(_CFG["zipf_exponent"] if exponent is None else exponent)
    if experts < 1 or tokens < 0 or exp <= 0:
        raise ProfilerUsageError("bench_routing_shape_invalid")
    weights = [1.0 / float(idx + 1) ** exp for idx in range(int(experts))]
    total = sum(weights)
    raw = [int(tokens) * w / total for w in weights]
    counts = [int(math.floor(v)) for v in raw]
    for i in sorted(range(int(experts)), key=lambda idx: (-(raw[idx] - counts[idx]), idx))[: max(0, int(tokens) - sum(counts))]:
        counts[i] += 1
    return counts


def _l0_case(idx: int, sku: str, arch: str, mode: str, spec: tuple[int, str, str, str, dict[str, Any], str, str, dict[str, Any]]) -> dict[str, Any]:
    dom, bld, abi_sym, dt, shp, lay, sp, ext = spec
    key = normalize_canonical_key({
        "sig_version": _SIG_VER, "kind": "operator", "sku": sku, "soc_arch": arch,
        "abi_backend": "cann_aclnn", "upstream_abi": abi_sym, "bench_builder": bld,
        "canonical_shapes": dict(shp), "dtypes": {"input": dt, "output": dt},
        "layouts": {"input": lay, "output": lay}, "per_expert_token_counts": ext.get("group_list"),
        "capture_mode": mode, "residency": "cold_hbm",
        "op_attrs": {k: v for k, v in ext.items() if k not in {"group_list", "work_bytes", "work_flops"}},
    })
    digest, cid = canonical_key_digest(key), canonical_case_id(key)
    node = {"node_id": "n0", "kind": "operator", "builder": bld, "op": bld, "upstream_abi": abi_sym,
            "abi_backend": "cann_aclnn", "dtype": dt, "layout": lay, "shape": dict(shp), **ext}
    return {
        "acquisition_uid": f"l0-{idx:04d}", "case_id": cid, "canonical_key_digest": digest,
        "canonical_key": key, "kind": "operator", "level": "L1", "boundary": "device_kernel",
        "split": sp, "phase": "decode" if mode == "aclgraph" else "prefill", "stage": "s0_local",
        "capture_mode": mode, "residency": "cold_hbm", "clock_operator": "elapsed_span",
        "work_flops": int(ext.get("work_flops") or 0), "work_bytes": int(ext.get("work_bytes") or 0),
        "nodes": [node], "edges": [], "timed_boundary": {"include": ["n0"]},
        "identities": {"domain": dom},
    }


def build_l0_plan(
    *, sku: str = DAV_2201, domains: Sequence[int] | None = None,
    dtypes: Sequence[str] | None = None, capture_modes: Sequence[str] = ("eager",),
) -> dict[str, Any]:
    """Emit a pure-data ``mindie-bench-plan/2`` for minimal L0 hardware presets."""
    if sku not in SUPPORTED_SKUS:
        raise ProfilerUsageError(f"bench_sku_unsupported: {sku!r}")
    arch, allowed = infer_soc_arch(sku), supported_dtypes_for_sku(sku)
    req_dt = list(dtypes) if dtypes else list(BASE_DTYPES)
    for dt in req_dt:
        if dt in A5_ONLY_FP8_DTYPES:
            validate_dtype_for_arch(dt, arch)
        if dt not in allowed:
            raise ProfilerUsageError(f"bench_dtype_unsupported: {dt!r}")
    sel = sorted(set(int(d) for d in (DOMAIN_IDS if domains is None else domains)))
    if any(d not in DOMAIN_IDS for d in sel):
        raise ProfilerUsageError(f"bench_domain_unknown: {sel}")
    d1, d2, d3, d5 = DOMAIN_IDS
    held_m, proto = set(int(v) for v in _CFG["heldout_m"]), _DMA.get(sku, "host_dma")
    specs: list[tuple[int, str, str, str, dict[str, Any], str, str, dict[str, Any]]] = []
    if d1 in sel:
        specs.extend([
            (d1, "empty_event_pair", "empty_event_pair", "bf16", {}, "ND", "train", {}),
            (d1, "vector_add", "aclnnAdd", "bf16", {"tokens": 1, "width": 1}, "ND", "train", {}),
            (d1, "rms_norm", "aclnnRmsNorm", "bf16", {"tokens": 1, "width": int(_CFG["d1_norm_width"])}, "ND", "train", {}),
        ])
    if d2 in sel:
        for dt in req_dt:
            for m, n, k in _CFG["gemm_shapes"]:
                specs.append((d2, "matmul", "aclnnMatmul", dt, {"m": int(m), "n": int(n), "k": int(k)}, "KN", "heldout" if int(m) in held_m else "train", {"work_flops": 2 * int(m) * int(n) * int(k)}))
    if d3 in sel:
        experts, k, n = _CFG["routing_expert_shapes"][0]
        toks = int(_CFG["routing_tokens"][1])
        for dt in req_dt:
            for dist, gl in (("uniform", uniform_counts(int(experts), toks)), ("zipf_s1.2", zipf_counts(int(experts), toks))):
                specs.append((d3, "grouped_matmul", "aclnnGroupedMatmulV5", dt, {"e": int(experts), "k": int(k), "n": int(n), "m": toks}, "ND", "train", {"group_list": gl, "group_list_type": 1, "distribution": dist}))
    if d5 in sel:
        for size in _CFG["pinned_copy_sizes"]:
            specs.append((d5, "pinned_copy", "aclrtMemcpyAsync", "bf16", {"bytes": int(size), "direction": "h2d", "transfer_protocol": proto}, "ND", "train", {"work_bytes": int(size), "direction": "h2d", "transfer_protocol": proto}))
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for mode in capture_modes:
        for spec in specs:
            c = _l0_case(len(cases) + 1, sku, arch, str(mode), spec)
            if c["case_id"] not in seen:
                seen.add(c["case_id"])
                cases.append(c)
    return seal_payload({
        "schema": PLAN_V2_SCHEMA, "plan_id": f"l0-{sku.lower()}", "plan_kind": "sku_onboarding",
        "sku": sku, "soc_arch": arch, "stage": "s0_local", "world_size": 1,
        "cache_partition": "shared", "training_manifest_sha256": None,
        "cases": cases, "reverse_index": {c["case_id"]: [] for c in cases},
    }, "plan_sha256")


__all__ = [
    "A2_SKUS", "A3_SKUS", "A5_EXTRA_DTYPES", "A5_SKUS", "BASE_DTYPES",
    "DAV_2201", "DOMAIN_IDS", "SUPPORTED_SKUS", "build_l0_plan",
    "supported_dtypes_for_sku", "uniform_counts", "zipf_counts",
]
