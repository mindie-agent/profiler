"""Unified incremental silicon benchmark campaign runner (<8 GiB, S0/S1).

[Role]
  Execute ``mindie-bench-plan/2`` and legacy ``mindie-bench-subgraph-plan/1``
  plans against a version-fingerprinted ``CampaignStore``, running ONLY the
  unmeasured delta in bounded ``<= 8 GiB`` per-case envelopes with verified
  cold-HBM eviction, traced ``busy_union`` vs ``elapsed_span`` labeling,
  multi-node S1 collective topology validation, guarded ``abi_rejection``
  execution, exact multiset conservation, and sealed ``mindie-bench-campaign/1``
  publication.  Also serves the thin ``bench sku`` CLI alias via ``l0_presets``.

[Invariants]
  * Pure CPU at import time (``DEV-ZERO-CTX``); imports ``torch`` /
    ``torch_npu`` lazily only during live execution.
  * Strips ``sim_reference`` and any ``predicted_*`` keys at ingress (after
    verifying ``plan_sha256``) and enforces outbound ``portable_receipt()``.
  * Never silently runs ``inter_node`` collective tiers on loopback; topology
    mismatch returns explicit ``status="unsupported"``.
  * Labels ``clock_operator="busy_union"`` ONLY when traced device kernel
    intervals are provided; raw event-pair/ACLGraph spans are ``elapsed_span``.
  * Conserves ``len(cases) + len(blocked_cases) + len(worker_diagnostics) ==
    len(planned_cases)`` with non-null integer ``rank`` on every row.

[Timeouts & Locks]
  Propagates ``TimeoutError`` on every guarded boundary; delegates bucket
  locking to ``CampaignStore`` (``storage_locks.exclusive_lock``).

[Side-Effect Policy]
  Writes immutable run shards under ``<campaign_dir>/buckets/<env_fp>/runs/``,
  atomically updates ``index.json`` and ``campaign_manifest.json`` via
  ``os.replace``, and optionally writes ``--out``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import gc
import json
import os
from pathlib import Path
import sys
from typing import Any
import uuid

from ..events import ProfilerUsageError
from .abi import resolve_allowed_phy_ids
from .abi_portable import capture_uri, portable_receipt, strip_caller_predictions
from .campaign_store import (
    CAMPAIGN_SCHEMA,
    PLAN_V2_SCHEMA,
    CampaignStore,
    canonical_case_id,
    canonical_key_digest,
    load_training_manifest_freeze,
    seal_case_raw_sha256,
    seal_payload,
    sha256_canonical,
    stream_shards_sha256,
    synthesize_canonical_key_from_v1_case,
    verify_case_canonical_key,
    verify_seal,
)
from .env_fingerprint import (
    CACHE_PARTITIONS,
    CPU_SMOKE_PROTOCOL_ID,
    DEFAULT_TIMING_PROTOCOL_ID,
    infer_soc_arch,
    is_live_clock_source,
    probe_env_fingerprint,
    validate_clock_band,
)
from .l0_presets import DAV_2201, build_l0_plan
from .observations import case_outcome_row_v2, observation_row_v2, timing_rows
from .operators import BenchUnmodeledOperatorError, build_operator_enqueue
from .operators_common import shape_of, validate_dtype_for_arch
from .profiles import profile_section
from .subgraph_runtime import (
    OperatorExecutor, TorchJointRuntime, execute_joint_case, execute_local_case, is_collective,
)
from .timing import (
    CLOCK_OPERATOR_BUSY_UNION,
    CLOCK_OPERATOR_ELAPSED_SPAN,
    HOST_FALLBACK,
    MIB,
    case_over_budget,
    estimate_working_set_bytes,
    make_l2_flush_op,
    measure_peak_allocated_bytes,
    reset_peak_memory_stats,
)
from .timing_ring import make_blocker_unit_op, resolve_l2_bytes

PLAN_V1_SCHEMA = "mindie-bench-subgraph-plan/1"
_CAMPAIGN_CFG = profile_section("campaign")
_SUBGRAPH_CFG = profile_section("subgraph")
_RUN_ID_CHARS = int(_CAMPAIGN_CFG["run_id_chars"])
_CAMP_ID_CHARS = int(_CAMPAIGN_CFG["campaign_id_chars"])
_REASON_LIMIT = int(_CAMPAIGN_CFG["max_text_chars"])
_DEFAULT_MASTER_PORT = int(_CAMPAIGN_CFG["default_master_port"])
_RDZV_TIMEOUT_S = float(_CAMPAIGN_CFG["rendezvous_timeout_s"])
_EXIT_ERR = int(_CAMPAIGN_CFG["exit_error"])
_EXIT_UNAVAIL = int(_CAMPAIGN_CFG["exit_torch_unavailable"])
_MAX_PLAN_BYTES = int(_SUBGRAPH_CFG["max_plan_bytes"])
_LOOPBACK_HOSTS = frozenset({"", "127.0.0.1", "localhost", "::1"})


def _empty_device_cache(torch: Any, torch_npu: Any = None) -> None:
    for holder in (getattr(torch, "npu", None) if torch is not None else None, torch_npu):
        cleaner = getattr(holder, "empty_cache", None) if holder is not None else None
        if callable(cleaner):
            try:
                cleaner()
                return
            except TimeoutError:
                raise
            except Exception:
                continue


def _verify_and_strip_plan(raw_plan: Mapping[str, Any]) -> dict[str, Any]:
    schema = str(raw_plan.get("schema") or "")
    if schema not in {PLAN_V2_SCHEMA, PLAN_V1_SCHEMA}:
        raise ProfilerUsageError(
            f"bench_plan_schema_invalid: expected {PLAN_V2_SCHEMA} or {PLAN_V1_SCHEMA}, got {schema!r}"
        )
    if schema == PLAN_V2_SCHEMA and raw_plan.get("plan_sha256"):
        if not verify_seal(raw_plan, "plan_sha256"):
            raise ProfilerUsageError("bench_plan_sha256_mismatch")
    plan_sha = str(raw_plan.get("plan_sha256") or sha256_canonical(raw_plan))
    clean = strip_caller_predictions(dict(raw_plan))
    clean["plan_sha256"] = plan_sha
    return clean


def _normalize_wire_edges(raw_edges: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for edge in raw_edges or ():
        if isinstance(edge, Mapping):
            out.append({
                "from": str(edge.get("from") or ""),
                "to": str(edge.get("to") or ""),
                "kind": str(edge.get("kind") or "data"),
            })
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            out.append({
                "from": str(edge[0]),
                "to": str(edge[1]),
                "kind": str(edge[2]) if len(edge) > 2 and edge[2] else "data",
            })
    return out


def _unrealized_stride_or_offset_reason(key: Mapping[str, Any]) -> str | None:
    offsets = key.get("storage_offsets")
    if isinstance(offsets, Mapping):
        for name, off in sorted(offsets.items()):
            if isinstance(off, int) and not isinstance(off, bool) and off != 0:
                return f"unrealized_storage_offset:{name}={off}"
    strides = key.get("strides")
    if isinstance(strides, Mapping):
        for name, dims in sorted(strides.items()):
            if not isinstance(dims, (list, tuple)) or not dims:
                continue
            vals = [int(v) for v in dims]
            if vals[-1] != 1 or any(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
                return f"unrealized_non_contiguous_stride:{name}={vals}"
    return None


def _validate_all_case_dtypes(case: Mapping[str, Any], soc_arch: str) -> None:
    seen: set[str] = set()
    key = case.get("canonical_key") if isinstance(case.get("canonical_key"), Mapping) else {}
    dtypes_map = key.get("dtypes") if isinstance(key.get("dtypes"), Mapping) else {}
    for val in dtypes_map.values():
        if isinstance(val, str) and val.strip():
            seen.add(val.strip())
    for field in ("dtype", "weight_dtype", "cache_dtype", "kv_dtype", "output_dtype"):
        val = case.get(field)
        if isinstance(val, str) and val.strip():
            seen.add(val.strip())
    for node in case.get("nodes") or ():
        if not isinstance(node, Mapping):
            continue
        for field in ("dtype", "weight_dtype", "cache_dtype", "kv_dtype", "output_dtype"):
            val = node.get(field)
            if isinstance(val, str) and val.strip():
                seen.add(val.strip())
        shp = node.get("shape") if isinstance(node.get("shape"), Mapping) else {}
        for field in ("dtype", "kv_dtype", "cache_dtype", "weight_dtype"):
            val = shp.get(field)
            if isinstance(val, str) and val.strip():
                seen.add(val.strip())
    for dt in sorted(seen):
        validate_dtype_for_arch(dt, soc_arch)


def _endpoint_host(endpoint: str) -> str:
    raw = str(endpoint or "").strip()
    if raw.startswith("[") and "]" in raw:
        return raw[1 : raw.index("]")].strip().lower()
    if ":" in raw:
        return raw.rsplit(":", 1)[0].strip().lower()
    return raw.lower()


def _load_raw_plan_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    try:
        if target.stat().st_size > _MAX_PLAN_BYTES:
            raise ProfilerUsageError("bench_plan_too_large")
        raw = json.loads(target.read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProfilerUsageError(f"bench_plan_invalid: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ProfilerUsageError("bench_plan_invalid: expected JSON object")
    return dict(raw)


def load_campaign_plan(path: str | Path) -> dict[str, Any]:
    """Load, verify ``plan_sha256``, and strip ``sim_reference`` / ``predicted_*``."""
    return normalize_plan(_load_raw_plan_json(path))


def normalize_plan(raw_plan: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize both ``mindie-bench-plan/2`` and ``mindie-bench-subgraph-plan/1`` plans."""
    clean = _verify_and_strip_plan(raw_plan)
    schema = str(clean.get("schema") or "")
    sku = str(clean.get("sku") or (clean.get("hardware") if isinstance(clean.get("hardware"), str) else "") or "unknown")
    soc_arch = str(clean.get("soc_arch") or infer_soc_arch(sku))
    raw_cases = clean.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ProfilerUsageError("bench_plan_cases_missing")

    normalized: list[dict[str, Any]] = []
    if schema == PLAN_V2_SCHEMA:
        for idx, item in enumerate(raw_cases):
            if not isinstance(item, Mapping):
                raise ProfilerUsageError("bench_plan_case_invalid")
            digest, case_id, key = verify_case_canonical_key(item)
            case = dict(item)
            case["canonical_key"] = key
            case["canonical_key_digest"] = digest
            case["case_id"] = case_id
            case.setdefault("acquisition_uid", f"acq-{idx + 1:04d}")
            case.setdefault("boundary", "device_kernel")
            case.setdefault("split", "train")
            case["capture_mode"] = key["capture_mode"]
            case["residency"] = key["residency"]
            case["execution_modes"] = [key["capture_mode"]]
            case["edges"] = _normalize_wire_edges(case.get("edges"))
            extra_comm: dict[str, Any] = {}
            if key.get("ordered_rank_placement") is not None:
                extra_comm["group_ranks"] = list(key["ordered_rank_placement"])
            if key.get("split_sizes") is not None:
                extra_comm["send_splits"] = list(key["split_sizes"])
                extra_comm["split_sizes"] = list(key["split_sizes"])
            if not case.get("nodes"):
                case["nodes"] = [{
                    "node_id": "n0",
                    "kind": "collective" if key["kind"] == "collective" else "operator",
                    "builder": key["bench_builder"],
                    "op": key["bench_builder"],
                    "upstream_abi": key["upstream_abi"],
                    "abi_backend": key["abi_backend"],
                    "dtype": str(key["dtypes"].get("input") or "bf16"),
                    "layout": str(key["layouts"].get("input") or "ND"),
                    "shape": dict(key["canonical_shapes"]),
                    "page_geometry": key.get("page_geometry"),
                    **({"group_list": list(key["per_expert_token_counts"])} if key.get("per_expert_token_counts") is not None else {}),
                    **extra_comm,
                }]
                case.setdefault("timed_boundary", {"include": ["n0"]})
            elif len(case["nodes"]) == 1 and isinstance(case["nodes"][0], Mapping):
                node = dict(case["nodes"][0])
                node.setdefault("node_id", "n0")
                node.setdefault("kind", "collective" if key["kind"] == "collective" else "operator")
                node.setdefault("builder", key["bench_builder"])
                node.setdefault("op", key["bench_builder"])
                node.setdefault("upstream_abi", key["upstream_abi"])
                node.setdefault("abi_backend", key["abi_backend"])
                node.setdefault("dtype", str(key["dtypes"].get("input") or "bf16"))
                node.setdefault("layout", str(key["layouts"].get("input") or "ND"))
                if not node.get("shape"):
                    node["shape"] = dict(key["canonical_shapes"])
                if node.get("page_geometry") is None and key.get("page_geometry") is not None:
                    node["page_geometry"] = key["page_geometry"]
                if node.get("group_list") is None and key.get("per_expert_token_counts") is not None:
                    node["group_list"] = list(key["per_expert_token_counts"])
                for ck, cv in extra_comm.items():
                    node.setdefault(ck, cv)
                case["nodes"] = [node]
            normalized.append(case)
    else:
        plan_modes = list(clean.get("execution_modes") or ["eager"])
        for idx, item in enumerate(raw_cases):
            if not isinstance(item, Mapping):
                raise ProfilerUsageError("bench_plan_case_invalid")
            modes = list(item.get("execution_modes") or plan_modes)
            residency = str(item.get("residency") or "cold_hbm")
            for mode in modes:
                key = synthesize_canonical_key_from_v1_case(
                    item, sku=sku, soc_arch=soc_arch, capture_mode=str(mode), residency=residency
                )
                digest = canonical_key_digest(key)
                case_id = canonical_case_id(key)
                case = dict(item)
                case["legacy_case_id"] = str(item.get("case_id") or f"v1-{idx}")
                case["acquisition_uid"] = str(item.get("acquisition_uid") or f"acq-v1-{idx + 1:04d}-{mode}")
                case["case_id"] = case_id
                case["canonical_key_digest"] = digest
                case["canonical_key"] = key
                case["capture_mode"] = key["capture_mode"]
                case["residency"] = key["residency"]
                case["execution_modes"] = [key["capture_mode"]]
                case.setdefault("boundary", "device_kernel")
                case.setdefault("split", "train")
                normalized.append(case)

    clean["sku"] = sku
    clean["soc_arch"] = soc_arch
    clean["cases"] = normalized
    clean.setdefault("cache_partition", "shared")
    clean.setdefault("stage", "s0_local")
    clean.setdefault("world_size", 1)
    return clean


def verify_collective_topology(
    case: Mapping[str, Any],
    *,
    world_size: int = 1,
    nnodes: int = 1,
    master_addr: str = "127.0.0.1",
    realized_rank_placement: Sequence[int] | None = None,
    realized_link_tiers: Sequence[str] | None = None,
) -> tuple[bool, str | None]:
    """Validate realized multi-node/rank topology against declared placement & link tiers."""
    key = case.get("canonical_key") if isinstance(case.get("canonical_key"), Mapping) else {}
    kind = str(key.get("kind") or case.get("kind") or "operator")
    placement = key.get("ordered_rank_placement")
    tiers = key.get("link_tiers")
    is_comm = kind in {"collective", "fabric"} or bool(placement) or bool(tiers)
    if not is_comm:
        return True, None
    tier_set = {str(t).strip().lower() for t in (tiers or ())}
    if "inter_node" in tier_set:
        host = str(master_addr or "").strip().lower()
        if int(nnodes) < 2 or host in _LOOPBACK_HOSTS:
            return False, "inter_node_requires_multi_node_rendezvous"
    if placement is not None:
        required = [int(r) for r in placement]
        if int(world_size) < len(required):
            return False, f"world_size_below_ordered_rank_placement:{world_size}<{len(required)}"
        if realized_rank_placement is not None:
            realized = [int(r) for r in realized_rank_placement]
            if realized != required:
                return False, f"realized_rank_placement_mismatch:{realized}!={required}"
    if tiers is not None and realized_link_tiers is not None:
        realized_tiers = {str(t).strip().lower() for t in realized_link_tiers}
        missing = sorted(tier_set - realized_tiers)
        if missing:
            return False, f"realized_link_tiers_missing:{','.join(missing)}"
    return True, None


def build_torchrun_command(
    *,
    plan_path: str | Path,
    campaign_dir: str | Path,
    world_size: int,
    nnodes: int = 1,
    node_rank: int = 0,
    master_addr: str | None = None,
    master_port: int = _DEFAULT_MASTER_PORT,
    rdzv_backend: str = "c10d",
    rdzv_endpoint: str | None = None,
    extra_args: Sequence[str] = (),
) -> list[str]:
    """Build a multi-node-capable ``torchrun`` rendezvous command (never hardcodes loopback on multi-node)."""
    if int(world_size) < 1 or int(nnodes) < 1:
        raise ProfilerUsageError("bench_torchrun_topology_invalid")
    if int(nnodes) > 1:
        eff_host = _endpoint_host(rdzv_endpoint) if rdzv_endpoint else str(master_addr or "").strip().lower()
        if eff_host in _LOOPBACK_HOSTS:
            raise ProfilerUsageError(
                "bench_multinode_master_addr_required: inter-node torchrun requires a non-loopback --master-addr or --rdzv-endpoint"
            )
        if int(world_size) % int(nnodes) != 0:
            raise ProfilerUsageError("bench_torchrun_world_not_divisible_by_nnodes")
    nproc = max(1, int(world_size) // int(nnodes))
    addr = str(master_addr or "127.0.0.1")
    cmd = [
        "torchrun",
        f"--nnodes={int(nnodes)}",
        f"--node-rank={int(node_rank)}",
        f"--nproc-per-node={nproc}",
        f"--rdzv-backend={rdzv_backend}",
    ]
    if rdzv_endpoint:
        cmd.append(f"--rdzv-endpoint={rdzv_endpoint}")
    else:
        cmd.extend([f"--master-addr={addr}", f"--master-port={int(master_port)}"])
    cmd.extend([
        "-m", "mindie_profiler", "bench", "run-plan",
        "--plan", str(plan_path),
        "--campaign-dir", str(campaign_dir),
        "--world-size", str(int(world_size)),
        "--nnodes", str(int(nnodes)),
        "--node-rank", str(int(node_rank)),
        "--master-addr", addr,
        "--master-port", str(int(master_port)),
        *list(extra_args),
    ])
    return cmd


def _primary_mode_summary(record: Mapping[str, Any], capture_mode: str) -> tuple[str, Mapping[str, Any]]:
    arm = record.get("aclgraph") if capture_mode == "aclgraph" else (record.get("eager") or record.get("timing"))
    if not isinstance(arm, Mapping):
        arm = record.get("timing") if isinstance(record.get("timing"), Mapping) else {}
    modes = arm.get("modes") if isinstance(arm.get("modes"), Mapping) else {}
    for pref in ("stream_saturated", "eager", HOST_FALLBACK):
        if pref in modes and isinstance(modes[pref], Mapping):
            return pref, modes[pref]
    for name, summary in modes.items():
        if isinstance(summary, Mapping):
            return str(name), summary
    return capture_mode, {}


def _build_blocked_entry(
    case: Mapping[str, Any],
    *,
    status: str,
    rank: int,
    observed_clock_mhz: float | None,
    clock_operator: str = CLOCK_OPERATOR_ELAPSED_SPAN,
    abi_rejected: bool = False,
    abi_error: str | None = None,
    reason: str | None = None,
    unmodeled_hint: Mapping[str, Any] | None = None,
    actual_shape: Mapping[str, Any] | None = None,
    hbm_peak_bytes: int | None = None,
    training_manifest_sha256: str | None = None,
    run_id: str | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "acquisition_uid": str(case["acquisition_uid"]),
        "case_id": str(case["case_id"]),
        "canonical_key_digest": str(case["canonical_key_digest"]),
        "boundary": str(case.get("boundary") or "device_kernel"),
        "split": str(case.get("split") or "train"),
        "capture_mode": str(case.get("capture_mode") or "eager"),
        "residency": str(case.get("residency") or "cold_hbm"),
        "status": str(status),
        "abi_rejected": bool(abi_rejected),
        "abi_error": abi_error,
        "reason": reason,
        "unmodeled_hint": dict(unmodeled_hint) if isinstance(unmodeled_hint, Mapping) else None,
        "stats_us": None,
        "measured_ns": None,
        "observed_clock_mhz": observed_clock_mhz,
        "clock_operator": clock_operator,
        "rank": int(rank),
        "actual_executed_shape": dict(actual_shape or {}),
        "hbm_peak_bytes": hbm_peak_bytes,
        "qualified": False,
        "cache_status": "measured",
    }
    if run_id is not None:
        entry["measured_in_run_id"] = str(run_id)
        entry["run_shard"] = f"runs/{run_id}.jsonl"
    if training_manifest_sha256 is not None:
        entry["training_manifest_sha256"] = training_manifest_sha256
    clean = portable_receipt(entry, home=os.environ.get("HOME") if home is None else home)
    return seal_case_raw_sha256(clean)


def _execute_abi_rejection_case(
    case: Mapping[str, Any],
    *,
    executor: Any,
    torch: Any,
    torch_npu: Any,
    soc_arch: str,
    rank: int,
    observed_clock_mhz: float | None,
    run_id: str,
    home: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Run ``split='abi_rejection'`` in a guarded try/except (propagating ``TimeoutError``)."""
    node = (case.get("nodes") or (case,))[0]
    context = getattr(executor, "context", None) if executor is not None else {}
    budget = context.get("budget") if isinstance(context, Mapping) else None
    if case_over_budget(case, budget):
        blocked = _build_blocked_entry(
            case,
            status="over_budget",
            rank=rank,
            observed_clock_mhz=observed_clock_mhz,
            abi_rejected=False,
            reason="case working set exceeds S0 HBM cap",
            run_id=run_id,
            home=home,
        )
        return blocked, True
    if isinstance(context, dict):
        context["_actual_shape"] = {}
    try:
        _validate_all_case_dtypes(case, soc_arch)
        if executor is not None and hasattr(executor, "build"):
            enqueue = executor.build(node)
        else:
            enqueue = build_operator_enqueue(torch, node, context)
        enqueue()
        sync = getattr(getattr(torch, "npu", None), "synchronize", None)
        if callable(sync):
            sync()
    except TimeoutError:
        raise
    except Exception as exc:
        _empty_device_cache(torch, torch_npu)
        msg = str(exc)
        low = msg.lower()
        is_oom = (
            isinstance(exc, MemoryError)
            or msg.startswith("bench_vram_budget_exceeded:")
            or "out of memory" in low
        )
        if is_oom:
            status, rejected = "over_budget", False
        elif isinstance(exc, OSError):
            status, rejected = "failed", False
        else:
            status, rejected = "abi_rejected", True
        hint = dict(exc.payload) if isinstance(exc, BenchUnmodeledOperatorError) else None
        actual = dict((context or {}).get("_actual_shape") or {})
        actual.pop("node_shapes", None)
        blocked = _build_blocked_entry(
            case,
            status=status,
            rank=rank,
            observed_clock_mhz=observed_clock_mhz,
            abi_rejected=rejected,
            abi_error=msg[:_REASON_LIMIT] if rejected else None,
            reason=msg[:_REASON_LIMIT],
            unmodeled_hint=hint,
            actual_shape=actual or shape_of(node),
            run_id=run_id,
            home=home,
        )
        return blocked, True
    _empty_device_cache(torch, torch_npu)
    diag = _build_blocked_entry(
        case,
        status="failed",
        rank=rank,
        observed_clock_mhz=observed_clock_mhz,
        abi_rejected=False,
        reason="abi_rejection_unexpected_pass: expected_abi_rejection_passed_unexpectedly",
        actual_shape=shape_of(node),
        run_id=run_id,
        home=home,
    )
    return diag, False


def _execute_measured_case(
    case: Mapping[str, Any],
    *,
    executor: Any,
    protocol: Any,
    runtime: Any,
    stage: str,
    soc_arch: str,
    rank: int,
    world_size: int,
    campaign_id: str,
    run_id: str,
    env_id: str,
    observed_clock_mhz: float | None,
    clock_source: str | None,
    nominal_clock_mhz: float | None,
    baseline_clock_mhz: float | None,
    l2_bytes: int | None,
    traced_intervals_provider: Callable[[Mapping[str, Any]], Sequence[Any] | None] | None = None,
    home: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    """[Cohesive-Pipeline] Execute one unmeasured case inside a bounded <8 GiB envelope."""
    context = getattr(executor, "context", None) if executor is not None else {}
    torch = getattr(executor, "torch", None) or (context.get("torch") if isinstance(context, Mapping) else None)
    torch_npu = context.get("torch_npu") if isinstance(context, Mapping) else None
    ordinal = int(((context.get("device") or {}) if isinstance(context, Mapping) else {}).get("ordinal") or 0)
    budget = context.get("budget") if isinstance(context, Mapping) else None
    cap_bytes = int(budget.get("cap_bytes") or 0) if isinstance(budget, Mapping) else 0
    capture_mode = str(case.get("capture_mode") or "eager")
    residency = str(case.get("residency") or "cold_hbm")
    node = (case.get("nodes") or (case,))[0]
    key = case["canonical_key"]

    reset = getattr(executor, "reset", None)
    if callable(reset):
        reset()
    if isinstance(context, dict):
        context.pop("_cold_coverage", None)
    _empty_device_cache(torch, torch_npu)
    reset_peak_memory_stats(torch_npu, ordinal, torch=torch)

    stride_reason = _unrealized_stride_or_offset_reason(key)
    if stride_reason:
        blocked = _build_blocked_entry(
            case, status="unsupported", rank=rank, observed_clock_mhz=observed_clock_mhz,
            reason=stride_reason, run_id=run_id, home=home,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"

    if case_over_budget(case, budget):
        blocked = _build_blocked_entry(
            case, status="over_budget", rank=rank, observed_clock_mhz=observed_clock_mhz,
            reason="case working set exceeds S0 HBM cap", run_id=run_id, home=home,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"

    dtype = str(node.get("dtype") or case.get("dtype") or "bf16")
    try:
        _validate_all_case_dtypes(case, soc_arch)
    except ProfilerUsageError as exc:
        blocked = _build_blocked_entry(
            case, status="abi_unsupported", rank=rank, observed_clock_mhz=observed_clock_mhz,
            abi_rejected=True, abi_error=str(exc)[:_REASON_LIMIT], reason=str(exc)[:_REASON_LIMIT],
            run_id=run_id, home=home,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"

    flush_op = None
    if residency == "cold_hbm" and l2_bytes:
        ring_obj = context.get("ring") if isinstance(context, Mapping) else None
        ring_bytes = int(getattr(ring_obj, "allocated_bytes", 0) or 0) if getattr(ring_obj, "allocated", False) else 0
        ws_bytes = estimate_working_set_bytes(case)
        flush_cap = max(0, cap_bytes - ring_bytes - ws_bytes) if cap_bytes > 0 else 0
        if cap_bytes == 0 or flush_cap > 0:
            flush_op = make_l2_flush_op(torch, l2_bytes, ordinal, cap_bytes=flush_cap)
        if isinstance(context, dict):
            context["explicit_l2_flush"] = callable(flush_op)

    traced_intervals = traced_intervals_provider(case) if callable(traced_intervals_provider) else None
    wrapped_protocol = _ProtocolAdapter(protocol, pre_repeat=flush_op, traced_intervals_us=traced_intervals)
    case_nodes = case.get("nodes") or ()
    has_collective = any(is_collective(n) for n in case_nodes if isinstance(n, Mapping))
    try:
        if (stage == "s1_joint" or has_collective) and runtime is not None:
            raw_rec = execute_joint_case(
                executor, case, wrapped_protocol, runtime,
                execution_modes=[capture_mode],
                blocker=context.get("blocker") if isinstance(context, Mapping) else None,
                blocker_receipt=context.get("blocker_receipt") if isinstance(context, Mapping) else None,
            )
        elif has_collective and len(case_nodes) == 1 and isinstance(context, Mapping) and context.get("dist") is not None:
            if isinstance(context, dict):
                context["_actual_shape"] = {}
                context.pop("_cold_coverage", None)
            enqueue = executor.build(node)
            t_rec = wrapped_protocol.run(
                enqueue,
                case_id=str(case["case_id"]),
                kind="collective",
                nbytes=int(case.get("work_bytes") or 0),
            )
            raw_rec = {
                "status": "ok",
                "qualified": bool(t_rec.get("qualified", True)),
                "validated": True,
                "timing": t_rec,
                "eager": t_rec,
                "actual_shape": dict(context.get("_actual_shape") or shape_of(node)),
                "timed_nodes": [str(node.get("node_id") or "n0")],
            }
        else:
            raw_rec = execute_local_case(
                executor, case, wrapped_protocol, runtime=runtime, execution_modes=[capture_mode],
            )
    except TimeoutError:
        raise
    except Exception as exc:
        _empty_device_cache(torch, torch_npu)
        status = "over_budget" if isinstance(exc, ProfilerUsageError) and str(exc).startswith("bench_vram_budget_exceeded:") else (
            "abi_unsupported" if isinstance(exc, ProfilerUsageError) else "failed"
        )
        hint = dict(exc.payload) if isinstance(exc, BenchUnmodeledOperatorError) else None
        blocked = _build_blocked_entry(
            case, status=status, rank=rank, observed_clock_mhz=observed_clock_mhz,
            abi_rejected=(status == "abi_unsupported"),
            abi_error=str(exc)[:_REASON_LIMIT] if status == "abi_unsupported" else None,
            reason=str(exc)[:_REASON_LIMIT], unmodeled_hint=hint, run_id=run_id,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"

    peak_bytes = measure_peak_allocated_bytes(torch_npu, ordinal, torch=torch)
    if peak_bytes is None and isinstance(context, Mapping):
        ledger = context.get("_byte_ledger")
        if isinstance(ledger, Mapping) and ledger.get("peak_bytes") is not None:
            peak_bytes = int(ledger["peak_bytes"])
    if cap_bytes > 0 and peak_bytes is not None and peak_bytes > cap_bytes:
        blocked = _build_blocked_entry(
            case, status="over_budget", rank=rank, observed_clock_mhz=observed_clock_mhz,
            reason=f"hbm_peak_bytes={peak_bytes} exceeded cap_bytes={cap_bytes}",
            hbm_peak_bytes=peak_bytes, run_id=run_id,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"

    timing_mode, summary = _primary_mode_summary(raw_rec, capture_mode)
    arm_timing = raw_rec.get("aclgraph") if capture_mode == "aclgraph" else (raw_rec.get("eager") or raw_rec.get("timing"))
    arm_timing = arm_timing if isinstance(arm_timing, Mapping) else {}
    stats_us = summary.get("stats_us") if isinstance(summary.get("stats_us"), Mapping) else {}
    p50_us = float(summary.get("p50_us", summary.get("median_us", float(raw_rec.get("minimum_ms", 0.0)) * 1000.0)))
    if p50_us <= 0.0:
        blocked = _build_blocked_entry(
            case,
            status="failed",
            rank=rank,
            observed_clock_mhz=observed_clock_mhz,
            reason=str(raw_rec.get("reason") or "non_positive_measured_duration"),
            actual_shape=dict(raw_rec.get("actual_shape") or shape_of(node)),
            hbm_peak_bytes=peak_bytes,
            run_id=run_id,
        )
        return blocked, [_outcome_row(blocked, env_id=env_id, plan_id=case.get("plan_id"), run_id=run_id, sku=case.get("sku"))], "blocked"
    p90_us = float(summary.get("p90_us", p50_us))
    p99_us = float(summary.get("p99_us", p90_us))
    min_us = float(summary.get("min_us", summary.get("minimum_us", p50_us)))
    iqr_us = float(summary.get("iqr_us", 0.0))
    cv_pct = float(summary.get("cv_pct", 0.0))
    clock_operator = (
        CLOCK_OPERATOR_BUSY_UNION
        if traced_intervals and arm_timing.get("clock_operator") == CLOCK_OPERATOR_BUSY_UNION
        else CLOCK_OPERATOR_ELAPSED_SPAN
    )

    unqualified_reasons: list[str] = []
    timer_source = str(arm_timing.get("timer_source") or "perf_counter_host_fallback")
    if timer_source != "torch.npu.Event(enable_timing=True)":
        unqualified_reasons.append(f"timer_source:{timer_source}")
    if raw_rec.get("shape_qualified") is False:
        unqualified_reasons.append(str(raw_rec.get("reason") or "shape_mismatch"))
    if capture_mode == "aclgraph":
        cap_status = str((raw_rec.get("capture") or {}).get("status") or "capture_failed")
        if cap_status != "captured" or raw_rec.get("outputs_agree") is not True:
            unqualified_reasons.append(f"aclgraph:{cap_status}:agree={raw_rec.get('outputs_agree')}")
    else:
        cap_status = "skipped"

    cold_cov = context.get("_cold_coverage") if isinstance(context, Mapping) else None
    if residency == "cold_hbm":
        if capture_mode == "aclgraph":
            cold_verified = bool(callable(flush_op))
        else:
            cold_verified = bool(
                callable(flush_op)
                or (isinstance(cold_cov, Mapping) and cold_cov.get("cold_coverage_verified") is True)
            )
        if not cold_verified:
            unqualified_reasons.append("cold_eviction_unverified")
    else:
        cold_verified = True

    if not is_live_clock_source(clock_source):
        unqualified_reasons.append(f"clock_not_live:{clock_source or 'unavailable'}")
    clock_ok, clock_reason = validate_clock_band(
        observed_clock_mhz,
        nominal_clock_mhz=nominal_clock_mhz,
        baseline_clock_mhz=baseline_clock_mhz,
    )
    if not clock_ok and clock_reason:
        unqualified_reasons.append(clock_reason)

    if raw_rec.get("qualified") is False:
        unqualified_reasons.append("runtime_unqualified")
    qualified = len(unqualified_reasons) == 0 and raw_rec.get("status") == "ok"

    obs_rows: list[dict[str, Any]] = []
    event_ids: list[str] = []
    actual_shape = dict(raw_rec.get("actual_shape") or shape_of(node))
    node_shapes = raw_rec.get("node_shapes") if isinstance(raw_rec.get("node_shapes"), Mapping) else None
    for mode_name, mode_q, trial_idx, rep_idx, rep_us in timing_rows(arm_timing):
        row = observation_row_v2(
            env_fingerprint_id=env_id,
            canonical_key_digest=str(case["canonical_key_digest"]),
            acquisition_uid=str(case["acquisition_uid"]),
            observed_clock_mhz=observed_clock_mhz,
            clock_operator=clock_operator,
            capture_mode=capture_mode,
            actual_executed_shape=actual_shape,
            node_shapes=node_shapes,
            hbm_peak_bytes=peak_bytes,
            cache_status="measured",
            cold_coverage_verified=cold_verified,
            plan_id=case.get("plan_id") or campaign_id,
            case={**case, "hardware": key.get("sku"), "builder": key.get("bench_builder"), "dtype": dtype, "shape": actual_shape},
            run_id=f"{run_id}.{capture_mode}.{mode_name}.t{trial_idx}",
            split=str(case.get("split") or "train"),
            boundary=str(case.get("boundary") or "device_kernel"),
            timing_mode=mode_name,
            residency=residency,
            trial=trial_idx,
            repeat_index=rep_idx,
            rank=int(rank),
            duration_ms=float(rep_us) / 1000.0,
            source=capture_uri(campaign_id, f"{case['case_id']}/{capture_mode}.{trial_idx}.{rep_idx}.json"),
            validated=bool(raw_rec.get("validated", True)),
            qualified=bool(qualified and mode_q),
            sku=key.get("sku"),
            level=str(case.get("level") or "L1"),
            phase=case.get("phase"),
            execution={"mode": mode_name, "capture_mode": capture_mode, "stage": stage},
            work_bytes=case.get("work_bytes"),
        )
        obs_rows.append(row)
        event_ids.append(str(row["sample_id"]))

    hot_ctrl = arm_timing.get("hot_control") if isinstance(arm_timing.get("hot_control"), Mapping) else {}
    traced_verified = bool(
        traced_intervals
        and clock_operator == CLOCK_OPERATOR_BUSY_UNION
        and arm_timing.get("traced_interval_verified", True) is True
    )
    if not traced_verified:
        clock_operator = CLOCK_OPERATOR_ELAPSED_SPAN
    timed_nodes_list = list(raw_rec.get("timed_nodes") or ()) or [str(node.get("node_id") or "n0")]
    placement = key.get("ordered_rank_placement")
    if isinstance(placement, (list, tuple)) and placement:
        part_ranks = [int(r) for r in placement]
    elif has_collective and world_size > 1:
        part_ranks = list(range(int(world_size)))
    else:
        part_ranks = [int(rank)]
    raw_entry = portable_receipt({
        "acquisition_uid": str(case["acquisition_uid"]),
        "case_id": str(case["case_id"]),
        "canonical_key_digest": str(case["canonical_key_digest"]),
        "cache_status": "measured",
        "measured_in_run_id": str(run_id),
        "run_shard": f"runs/{run_id}.jsonl",
        "level": str(case.get("level") or "L1"),
        "boundary": str(case.get("boundary") or "device_kernel"),
        "split": str(case.get("split") or "train"),
        "status": "ok",
        "validated": bool(raw_rec.get("validated", True)),
        "qualified": bool(qualified),
        "unqualified_reasons": sorted(set(unqualified_reasons)),
        "abi_backend": str(key.get("abi_backend") or ""),
        "upstream_abi": str(key.get("upstream_abi") or ""),
        "bench_builder": str(key.get("bench_builder") or ""),
        "family": str(node.get("family") or case.get("family") or ""),
        "geometry_key": str(case.get("geometry_key") or case["canonical_key_digest"]),
        "capture_mode": capture_mode,
        "timing_mode": timing_mode,
        "residency": residency,
        "cold_coverage_verified": bool(cold_verified),
        **({"cold_coverage": dict(cold_cov)} if isinstance(cold_cov, Mapping) else {}),
        "traced_interval_verified": traced_verified,
        "clock_operator": clock_operator,
        "timer_source": timer_source,
        "rank": int(rank),
        "participating_ranks": part_ranks,
        "p50_us": p50_us,
        "p90_us": p90_us,
        "p99_us": p99_us,
        "min_us": min_us,
        "iqr_us": iqr_us,
        "cv_pct": cv_pct,
        "samples_count": max(1, int(summary.get("repeat_count") or len(obs_rows))),
        "stats_us": dict(stats_us) if stats_us else {
            "min": min_us, "p25": p50_us, "p50": p50_us, "p75": p50_us,
            "p90": p90_us, "p99": p99_us, "max": p99_us, "iqr": iqr_us, "cv_pct": cv_pct,
        },
        "measured_ns": int(round(p50_us * 1000.0)),
        "measured_p99_ns": int(round(p99_us * 1000.0)),
        "hot_control_p50_us": hot_ctrl.get("median_us"),
        "hbm_peak_bytes": peak_bytes,
        "hbm_budget_cap_bytes": cap_bytes or None,
        "observed_clock_mhz": observed_clock_mhz,
        "capture_status": cap_status,
        "outputs_agree": raw_rec.get("outputs_agree"),
        "actual_executed_shape": actual_shape,
        "node_shapes": dict(node_shapes) if node_shapes else {},
        "timed_nodes": timed_nodes_list,
        "event_ids": event_ids,
        "capture_uri": capture_uri(campaign_id, f"{case['case_id']}.json"),
    }, home=os.environ.get("HOME") if home is None else home)
    entry = seal_case_raw_sha256(raw_entry)
    return entry, obs_rows, "cases"


def _outcome_row(
    entry: Mapping[str, Any], *, env_id: str, plan_id: Any, run_id: str, sku: Any
) -> dict[str, Any]:
    return case_outcome_row_v2(
        env_fingerprint_id=env_id,
        plan_id=plan_id,
        run_id=run_id,
        acquisition_uid=str(entry["acquisition_uid"]),
        case_id=str(entry["case_id"]),
        canonical_key_digest=str(entry["canonical_key_digest"]),
        boundary=str(entry.get("boundary") or "device_kernel"),
        split=str(entry.get("split") or "train"),
        status=str(entry["status"]),
        capture_mode=str(entry.get("capture_mode") or "eager"),
        residency=str(entry.get("residency") or "cold_hbm"),
        rank=int(entry.get("rank", 0)),
        sku=sku,
        observed_clock_mhz=entry.get("observed_clock_mhz"),
        clock_operator=str(entry.get("clock_operator") or CLOCK_OPERATOR_ELAPSED_SPAN),
        abi_rejected=bool(entry.get("abi_rejected")),
        abi_error=entry.get("abi_error"),
        reason=entry.get("reason"),
        unmodeled_hint=entry.get("unmodeled_hint"),
        actual_executed_shape=entry.get("actual_executed_shape"),
        hbm_peak_bytes=entry.get("hbm_peak_bytes"),
    )


class _ProtocolAdapter:
    """Forwards ``pre_repeat`` and ``traced_intervals_us`` when supported by ``protocol``."""

    def __init__(
        self,
        inner: Any,
        *,
        pre_repeat: Callable[[], Any] | None = None,
        traced_intervals_us: Sequence[tuple[float, float]] | None = None,
    ) -> None:
        self._inner = inner
        self._pre_repeat = pre_repeat
        self._traced = traced_intervals_us

    def run(self, enqueue: Callable[[], Any], **kwargs: Any) -> dict[str, Any]:
        extra: dict[str, Any] = {}
        if self._pre_repeat is not None:
            extra["pre_repeat"] = self._pre_repeat
        if self._traced is not None:
            extra["traced_intervals_us"] = self._traced
        if extra:
            try:
                return self._inner.run(enqueue, **kwargs, **extra)
            except TypeError:
                pass
        return self._inner.run(enqueue, **kwargs)


def _collective_cache_hit_consensus(
    local_hit: bool, *, runtime: Any, world_size: int
) -> bool:
    """Require unanimous rank agreement before skipping a multi-rank collective."""
    if world_size <= 1 or runtime is None:
        return local_hit
    dist = getattr(runtime, "dist", None)
    all_gather_obj = getattr(dist, "all_gather_object", None) if dist is not None else None
    if callable(all_gather_obj):
        flags = [False] * int(world_size)
        all_gather_obj(flags, bool(local_hit))
        return all(bool(item) for item in flags)
    return False


def _run_normalized_campaign(
    plan: Mapping[str, Any],
    *,
    campaign_dir: str | Path,
    env_fingerprint: Mapping[str, Any],
    executor: Any = None,
    protocol: Any = None,
    runtime: Any = None,
    stage: str | None = None,
    rank: int = 0,
    world_size: int = 1,
    nnodes: int = 1,
    master_addr: str = "127.0.0.1",
    realized_rank_placement: Sequence[int] | None = None,
    realized_link_tiers: Sequence[str] | None = None,
    training_manifest: str | Path | Mapping[str, Any] | None = None,
    force_remeasure: bool = False,
    retry_unsupported: bool = False,
    l2_bytes: int | None = None,
    nominal_clock_mhz: float | None = None,
    run_id: str | None = None,
    traced_intervals_provider: Callable[[Mapping[str, Any]], Sequence[Any] | None] | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    """[Cohesive-Pipeline] Execute ONLY the unmeasured delta of normalized ``plan``."""
    resolved_home = os.environ.get("HOME") if home is None else home
    store = CampaignStore(campaign_dir)
    clean_env = store.ensure_bucket(env_fingerprint, nominal_clock_mhz=nominal_clock_mhz, home=resolved_home)
    env_id = str(clean_env["env_fingerprint_id"])
    bucket_index = store.load_index(env_id)
    baseline_clock = bucket_index.get("baseline_clock_mhz")
    nominal_clock = nominal_clock_mhz if nominal_clock_mhz is not None else bucket_index.get("nominal_clock_mhz")
    obs_clock = clean_env.get("observed_clock_mhz")
    clock_source = clean_env.get("clock_source")
    soc_arch = str(clean_env.get("soc_arch") or plan.get("soc_arch") or "unknown")
    active_stage = str(stage or plan.get("stage") or "s0_local")
    resolved_run_id = str(run_id or f"run-{uuid.uuid4().hex[:_RUN_ID_CHARS]}")
    campaign_id = f"camp-{uuid.uuid4().hex[:_CAMP_ID_CHARS]}"

    train_sha, train_digests, train_geoms = load_training_manifest_freeze(training_manifest)
    plan_tm_sha = plan.get("training_manifest_sha256")
    if plan_tm_sha is not None:
        if train_sha != str(plan_tm_sha):
            raise ProfilerUsageError(
                f"bench_training_manifest_sha256_mismatch: plan={plan_tm_sha!r} supplied={train_sha!r}"
            )
    plan_train_digests = {
        str(c["canonical_key_digest"]) for c in plan["cases"] if str(c.get("split") or "") == "train"
    }
    plan_train_geoms = {
        str(c["geometry_key"]) for c in plan["cases"]
        if str(c.get("split") or "") == "train" and c.get("geometry_key")
    }
    forbidden_heldout_digests = train_digests | plan_train_digests
    forbidden_heldout_geoms = train_geoms | plan_train_geoms

    cases_out: list[dict[str, Any]] = []
    blocked_out: list[dict[str, Any]] = []
    diag_out: list[dict[str, Any]] = []
    new_obs_rows: list[dict[str, Any]] = []
    new_index_entries: list[dict[str, Any]] = []
    hits = 0
    executed = 0

    for case in plan["cases"]:
        digest = str(case["canonical_key_digest"])
        mode = str(case["capture_mode"])
        residency = str(case["residency"])
        boundary = str(case.get("boundary") or "device_kernel")
        split = str(case.get("split") or "train")
        gkey = str(case.get("geometry_key") or "")
        case_with_plan = {**case, "plan_id": plan.get("plan_id"), "sku": plan.get("sku")}

        is_heldout = split == "heldout" or clean_env.get("cache_partition") == "heldout"
        if is_heldout and (digest in forbidden_heldout_digests or (gkey and gkey in forbidden_heldout_geoms)):
            blocked = _build_blocked_entry(
                case_with_plan,
                status="blocked",
                rank=rank,
                observed_clock_mhz=obs_clock,
                reason="heldout_training_overlap: geometry appears in frozen training_manifest_sha256",
                training_manifest_sha256=train_sha,
                run_id=resolved_run_id,
                home=resolved_home,
            )
            blocked_out.append(blocked)
            new_obs_rows.append(_outcome_row(blocked, env_id=env_id, plan_id=plan.get("plan_id"), run_id=resolved_run_id, sku=plan.get("sku")))
            continue

        topo_ok, topo_reason = verify_collective_topology(
            case_with_plan,
            world_size=world_size,
            nnodes=nnodes,
            master_addr=master_addr,
            realized_rank_placement=realized_rank_placement,
            realized_link_tiers=realized_link_tiers,
        )
        if not topo_ok:
            blocked = _build_blocked_entry(
                case_with_plan,
                status="unsupported",
                rank=rank,
                observed_clock_mhz=obs_clock,
                reason=topo_reason,
                run_id=resolved_run_id,
                home=resolved_home,
            )
            blocked_out.append(blocked)
            new_obs_rows.append(_outcome_row(blocked, env_id=env_id, plan_id=plan.get("plan_id"), run_id=resolved_run_id, sku=plan.get("sku")))
            continue

        case_nodes = case.get("nodes") or ()
        is_comm_case = any(is_collective(n) for n in case_nodes if isinstance(n, Mapping))
        if not force_remeasure:
            cached = store.lookup(
                env_id,
                digest,
                mode,
                residency,
                boundary=boundary,
                split=split,
                retry_unsupported=retry_unsupported,
                nominal_clock_mhz=nominal_clock,
                baseline_clock_mhz=baseline_clock,
                index_snapshot=bucket_index,
            )
            if is_comm_case and world_size > 1:
                agreed = _collective_cache_hit_consensus(
                    cached is not None, runtime=runtime, world_size=world_size
                )
                if not agreed:
                    cached = None
            if cached is not None:
                hits += 1
                cached["split"] = split
                if cached.get("status") == "ok":
                    cases_out.append(cached)
                else:
                    blocked_out.append(cached)
                continue

        executed += 1
        if split == "abi_rejection":
            torch = getattr(executor, "torch", None) if executor is not None else None
            torch_npu = (getattr(executor, "context", None) or {}).get("torch_npu") if executor is not None else None
            entry, was_rejected = _execute_abi_rejection_case(
                case_with_plan,
                executor=executor,
                torch=torch,
                torch_npu=torch_npu,
                soc_arch=soc_arch,
                rank=rank,
                observed_clock_mhz=obs_clock,
                run_id=resolved_run_id,
                home=resolved_home,
            )
            new_obs_rows.append(_outcome_row(entry, env_id=env_id, plan_id=plan.get("plan_id"), run_id=resolved_run_id, sku=plan.get("sku")))
            if was_rejected:
                blocked_out.append(entry)
                if entry.get("status") == "abi_rejected":
                    new_index_entries.append(entry)
            else:
                diag_out.append(entry)
            continue

        if executor is None or protocol is None:
            raise ProfilerUsageError("bench_runner_requires_executor_and_protocol")
        entry, rows, dest = _execute_measured_case(
            case_with_plan,
            executor=executor,
            protocol=protocol,
            runtime=runtime,
            stage=active_stage,
            soc_arch=soc_arch,
            rank=rank,
            world_size=world_size,
            campaign_id=campaign_id,
            run_id=resolved_run_id,
            env_id=env_id,
            observed_clock_mhz=obs_clock,
            clock_source=clock_source,
            nominal_clock_mhz=nominal_clock,
            baseline_clock_mhz=baseline_clock,
            l2_bytes=l2_bytes,
            traced_intervals_provider=traced_intervals_provider,
            home=resolved_home,
        )
        new_obs_rows.extend(rows)
        new_index_entries.append(entry)
        if dest == "cases":
            cases_out.append(entry)
        else:
            blocked_out.append(entry)
        if executor is not None and callable(getattr(executor, "reset", None)):
            executor.reset()
        gc.collect()

    all_shards = list(bucket_index.get("run_shards") or [])
    commit: dict[str, Any] | None = None
    if new_obs_rows or new_index_entries or not all_shards:
        commit = store.commit_run(
            clean_env,
            run_id=resolved_run_id,
            observation_rows=new_obs_rows,
            case_entries=new_index_entries,
            nominal_clock_mhz=nominal_clock,
            home=resolved_home,
        )
        all_shards = list(commit["run_shards"])
    shard_by_run = {item["run_id"]: item for item in all_shards}
    referenced_shards: list[dict[str, Any]] = []
    seen_runs: set[str] = set()
    for item in (*cases_out, *blocked_out, *diag_out):
        rid = str(item.get("measured_in_run_id") or resolved_run_id)
        if rid not in shard_by_run:
            raise ProfilerUsageError(f"bench_missing_run_shard_descriptor: {rid}")
        if rid not in seen_runs:
            seen_runs.add(rid)
            referenced_shards.append(shard_by_run[rid])
    if commit is not None and resolved_run_id not in seen_runs and resolved_run_id in shard_by_run:
        referenced_shards.append(shard_by_run[resolved_run_id])

    if len(referenced_shards) == 1:
        obs_relpath = str(referenced_shards[0]["path"])
        obs_sha256 = str(referenced_shards[0]["observations_sha256"])
    elif len(referenced_shards) > 1:
        obs_relpath = str(commit["shard_relpath"]) if commit is not None else str(referenced_shards[-1]["path"])
        obs_sha256 = stream_shards_sha256(
            store.bucket_dir(env_id), [str(item["path"]) for item in referenced_shards]
        )
    else:
        obs_relpath = str(commit["shard_relpath"]) if commit is not None else f"runs/{resolved_run_id}.jsonl"
        obs_sha256 = str(commit["observations_sha256"]) if commit is not None else sha256_canonical({})

    clock_ops = {str(item.get("clock_operator") or CLOCK_OPERATOR_ELAPSED_SPAN) for item in cases_out}
    manifest_clock_op = (
        CLOCK_OPERATOR_BUSY_UNION
        if clock_ops == {CLOCK_OPERATOR_BUSY_UNION}
        else CLOCK_OPERATOR_ELAPSED_SPAN
    )
    manifest_body = portable_receipt({
        "schema": CAMPAIGN_SCHEMA,
        "campaign_id": campaign_id,
        "run_id": resolved_run_id,
        "env_fingerprint_id": env_id,
        "cache_partition": str(clean_env.get("cache_partition") or "shared"),
        "plan_id": plan.get("plan_id"),
        "plan_sha256": plan["plan_sha256"],
        "training_manifest_sha256": train_sha,
        "version_fingerprint": clean_env,
        "clock_operator": manifest_clock_op,
        "observations_jsonl": obs_relpath,
        "observations_sha256": obs_sha256,
        "run_shards": referenced_shards,
        "planned_case_count": len(plan["cases"]),
        "cache_hit_count": hits,
        "executed_case_count": executed,
        "cases": cases_out,
        "blocked_cases": blocked_out,
        "worker_diagnostics": diag_out,
    }, home=resolved_home)
    sealed = seal_payload(manifest_body, "campaign_sha256")
    manifest_path = store.bucket_dir(env_id) / "campaign_manifest.json"
    _atomic_write_json(manifest_path, sealed)
    return sealed


def run_campaign(
    raw_plan: Mapping[str, Any],
    *,
    campaign_dir: str | Path,
    env_fingerprint: Mapping[str, Any],
    executor: Any = None,
    protocol: Any = None,
    runtime: Any = None,
    stage: str | None = None,
    rank: int = 0,
    world_size: int = 1,
    nnodes: int = 1,
    master_addr: str = "127.0.0.1",
    realized_rank_placement: Sequence[int] | None = None,
    realized_link_tiers: Sequence[str] | None = None,
    training_manifest: str | Path | Mapping[str, Any] | None = None,
    force_remeasure: bool = False,
    retry_unsupported: bool = False,
    l2_bytes: int | None = None,
    nominal_clock_mhz: float | None = None,
    run_id: str | None = None,
    traced_intervals_provider: Callable[[Mapping[str, Any]], Sequence[Any] | None] | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    """Execute ONLY the unmeasured delta of ``raw_plan`` and publish ``mindie-bench-campaign/1``."""
    return _run_normalized_campaign(
        normalize_plan(raw_plan),
        campaign_dir=campaign_dir,
        env_fingerprint=env_fingerprint,
        executor=executor,
        protocol=protocol,
        runtime=runtime,
        stage=stage,
        rank=rank,
        world_size=world_size,
        nnodes=nnodes,
        master_addr=master_addr,
        realized_rank_placement=realized_rank_placement,
        realized_link_tiers=realized_link_tiers,
        training_manifest=training_manifest,
        force_remeasure=force_remeasure,
        retry_unsupported=retry_unsupported,
        l2_bytes=l2_bytes,
        nominal_clock_mhz=nominal_clock_mhz,
        run_id=run_id,
        traced_intervals_provider=traced_intervals_provider,
        home=home,
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    if output:
        target = Path(output)
        _atomic_write_json(target, payload)
        print(json.dumps({"output": str(target), "status": payload.get("status", "ok")}, sort_keys=True))
        return
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _run_plan_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench run-plan",
        description="Execute a mindie-bench-plan/2 or /1 incrementally inside a version-fingerprinted campaign store.",
        allow_abbrev=False,
    )
    parser.add_argument("--plan", required=True, help="input mindie-bench-plan/2 or /1 JSON")
    parser.add_argument("--campaign-dir", required=True, help="content-addressed campaign store directory")
    parser.add_argument("--stage", default=None, choices=("s0_local", "s1_joint", "auto"))
    parser.add_argument("--cache-partition", default=None, choices=CACHE_PARTITIONS)
    parser.add_argument("--training-manifest", default=None, help="frozen training manifest for heldout independence")
    parser.add_argument("--va-commit", default=None, help="explicit vllm-ascend revision override")
    parser.add_argument("--allowed-phy-ids", default=None)
    parser.add_argument("--l2-mib", type=float, default=None)
    parser.add_argument("--world-size", type=int, default=1)
    parser.add_argument("--nnodes", type=int, default=1)
    parser.add_argument("--node-rank", type=int, default=0)
    parser.add_argument("--master-addr", default="127.0.0.1")
    parser.add_argument("--master-port", type=int, default=_DEFAULT_MASTER_PORT)
    parser.add_argument("--force-remeasure", action="store_true")
    parser.add_argument("--retry-unsupported", action="store_true")
    parser.add_argument("--allow-cpu-smoke", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", "--output", dest="output", default=None)
    return parser


def _execute_cli_plan(plan: Mapping[str, Any], args: argparse.Namespace) -> int:
    if args.dry_run:
        summary = portable_receipt({
            "schema": CAMPAIGN_SCHEMA,
            "status": "dry_run",
            "plan_id": plan.get("plan_id"),
            "plan_sha256": plan.get("plan_sha256"),
            "sku": plan.get("sku"),
            "case_count": len(plan["cases"]),
            "cases": [
                {
                    "acquisition_uid": c["acquisition_uid"],
                    "case_id": c["case_id"],
                    "canonical_key_digest": c["canonical_key_digest"],
                    "capture_mode": c["capture_mode"],
                    "split": c["split"],
                }
                for c in plan["cases"]
            ],
        }, home=os.environ.get("HOME"))
        _emit(summary, args.output)
        return 0
    try:
        import torch
        import torch_npu  # noqa: F401
    except TimeoutError:
        raise
    except Exception as exc:
        _emit({"schema": CAMPAIGN_SCHEMA, "status": "torch_npu_unavailable", "reason": str(exc)[:_REASON_LIMIT]}, args.output)
        return _EXIT_UNAVAIL
    from .abi import device_properties
    from .bench_archetype_subgraphs import _calibrate_context_blocker
    from .timing import admit_context, close_context

    if int(args.nnodes) > 1 and str(args.master_addr or "").strip().lower() in _LOOPBACK_HOSTS:
        raise ProfilerUsageError(
            "bench_multinode_master_addr_required: inter-node run-plan requires a non-loopback --master-addr"
        )
    plan_partition = str(plan.get("cache_partition") or "shared")
    effective_partition = str(args.cache_partition or plan_partition)
    if plan_partition == "heldout" and effective_partition != "heldout":
        raise ProfilerUsageError("bench_heldout_partition_override_forbidden")

    l2_bytes = int(args.l2_mib * MIB) if args.l2_mib is not None else resolve_l2_bytes(None, sku=str(plan.get("sku") or ""), torch_npu=torch_npu)
    context = admit_context(
        torch=torch,
        torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=l2_bytes,
        allocate=bool(l2_bytes is not None and not args.allow_cpu_smoke),
        allow_cpu_smoke=bool(args.allow_cpu_smoke),
    )
    rank = int(os.environ.get("RANK", "0"))
    world = int(os.environ.get("WORLD_SIZE", str(args.world_size)))
    context.update({"rank": rank, "world_size": world, "l2_bytes": l2_bytes})
    if not args.allow_cpu_smoke:
        context["blocker_unit_op"] = make_blocker_unit_op(torch, context["device"]["ordinal"])
        _calibrate_context_blocker(context, auto_unit_op=True)
    props = device_properties(torch_npu, context["device"]["ordinal"], torch=torch)
    hw_sku = str(props.get("name") or plan.get("sku") or "unknown")
    env_fp = probe_env_fingerprint(
        sku=hw_sku,
        device_properties=props,
        torch=torch,
        torch_npu=torch_npu,
        explicit_va_commit=args.va_commit,
        timing_protocol_id=CPU_SMOKE_PROTOCOL_ID if args.allow_cpu_smoke else DEFAULT_TIMING_PROTOCOL_ID,
        cache_partition=effective_partition,
        physical_id=context["device"].get("physical_id"),
    )
    try:
        runtime = TorchJointRuntime(torch, rank=rank, world_size=world, cases=plan["cases"], timeout_s=_RDZV_TIMEOUT_S)
        runtime.init_process_group()
        context.update({"dist": runtime.dist, "groups": runtime.groups, "dist_initialized": runtime.initialized})
        executor = OperatorExecutor(torch, context)
        try:
            manifest = _run_normalized_campaign(
                plan,
                campaign_dir=args.campaign_dir,
                env_fingerprint=env_fp,
                executor=executor,
                protocol=context["protocol"],
                runtime=runtime,
                stage=None if args.stage == "auto" else args.stage,
                rank=rank,
                world_size=world,
                nnodes=int(args.nnodes),
                master_addr=str(args.master_addr),
                training_manifest=args.training_manifest,
                force_remeasure=bool(args.force_remeasure),
                retry_unsupported=bool(args.retry_unsupported),
                l2_bytes=l2_bytes,
                nominal_clock_mhz=props.get("clock_mhz"),
            )
        finally:
            executor.reset()
            runtime.close()
    finally:
        close_context(context)
    _emit(manifest, args.output)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry for ``mindie-profiler bench run-plan``."""
    args = _run_plan_parser().parse_args(list(argv or ()))
    plan = load_campaign_plan(args.plan)
    return _execute_cli_plan(plan, args)


def _sku_alias_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench sku",
        description="Thin L0 preset CLI alias delegating 100% execution to campaign_runner.",
        allow_abbrev=False,
    )
    parser.add_argument("--sku", default=DAV_2201)
    parser.add_argument("--domain", type=int, action="append", default=None)
    parser.add_argument("--dtype", action="append", default=None)
    parser.add_argument("--campaign-dir", default=".mindie-bench-campaign")
    parser.add_argument("--cache-partition", default=None, choices=CACHE_PARTITIONS)
    parser.add_argument("--training-manifest", default=None)
    parser.add_argument("--va-commit", default=None)
    parser.add_argument("--allowed-phy-ids", default=None)
    parser.add_argument("--l2-mib", type=float, default=None)
    parser.add_argument("--force-remeasure", action="store_true")
    parser.add_argument("--retry-unsupported", action="store_true")
    parser.add_argument("--allow-cpu-smoke", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", "--output", dest="output", default=None)
    return parser


def main_sku(argv: Sequence[str] | None = None) -> int:
    """Thin zero-logic CLI alias for ``mindie-profiler bench sku``."""
    args = _sku_alias_parser().parse_args(list(argv or ()))
    plan = build_l0_plan(sku=args.sku, domains=args.domain, dtypes=args.dtype)
    if args.limit is not None:
        if args.limit < 0:
            raise ProfilerUsageError("bench_limit_invalid")
        sliced = plan["cases"][: args.limit]
        plan = seal_payload(
            {**plan, "cases": sliced, "reverse_index": {c["case_id"]: [] for c in sliced}},
            "plan_sha256",
        )
    normalized = normalize_plan(plan)
    args.stage = "s0_local"
    args.world_size = 1
    args.nnodes = 1
    args.node_rank = 0
    args.master_addr = "127.0.0.1"
    args.master_port = _DEFAULT_MASTER_PORT
    return _execute_cli_plan(normalized, args)


__all__ = [
    "PLAN_V1_SCHEMA",
    "build_torchrun_command",
    "load_campaign_plan",
    "main",
    "main_sku",
    "normalize_plan",
    "run_campaign",
    "verify_collective_topology",
]
