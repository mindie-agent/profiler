"""Scoped critical-owner KvQuantSparseFlashAttention MTE1 resource service.

[Role]
  Compute exact per-owner QK/PV L1->L0A/L0B critical-owner bytes in closed form
  from an explicit query geometry and summarize complete R64 prefill/dynamic
  ``KvQuantSparseFlashAttention`` PMU events whose full Q/KV/output tensor
  signatures match the declared geometry.

[Invariants]
  * ``sparse_geometry`` must be supplied explicitly and validated strictly
    (malformed or out-of-range fields raise ``ProfilerUsageError`` rather than
    silently returning ``[]``).
  * Only certified R64 captures (``source_scope == 'r64'``) in ``prefill`` /
    ``dynamic`` scope emit a sparse MTE1 service; non-R64, decode/static, and
    tensor-geometry mismatches emit explicit limitation codes before or after
    bounded candidate matching.
  * When ``sparse_geometry`` is omitted, ``SparseSupplyAccumulator`` retains
    zero candidate dicts (``O(1)`` memory).

[Timeouts & Locks]
  Closed-form ``O(q_len)`` integer arithmetic (``q_len <= 1,048,576``) and
  bounded sample retention (``<= 512``); no I/O or locks.

[Side-Effect Policy]
  Returns fresh dicts/lists or mutates only caller-owned accumulators.
"""

from __future__ import annotations

import statistics
from typing import Any, Iterable, Mapping, Sequence

from .events import Event, Observation, ProfilerQueryError, ProfilerUsageError
from .measured_supply import (
    R64_IMAGE_SHA,
    SATURATION_THRESHOLD,
    MatrixSupplyAccumulator,
    _dtype_slots,
    summarize_measured_supply,
)

RESOURCE_SERVICE_SCHEMA = "mindie-profiler-resource-service/1"
SPARSE_NATIVE_TYPE = "KvQuantSparseFlashAttention"
MAX_SPARSE_TOKENS = 1_048_576
MAX_SPARSE_DIM = 65_536
MAX_SPARSE_OWNERS = 4_096
MAX_SPARSE_GROUPS = 64
MAX_SPARSE_SAMPLES = 512


def _strict_int(mapping: Mapping[str, Any], key: str, default: int | None = None) -> int:
    if key not in mapping or mapping[key] is None:
        if default is not None:
            return default
        raise ProfilerUsageError(f"sparse_geometry missing required integer field: {key}")
    raw = mapping[key]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ProfilerUsageError(
            f"sparse_geometry.{key} must be an integer, got {type(raw).__name__}"
        )
    return raw


def _validate_geometry_scalars(
    *,
    q_len: int,
    context: int,
    kv_len: int,
    owners: int,
    g: int,
    dq: int,
    dv: int,
    s2_tile: int,
) -> None:
    for name, val in (
        ("q_len", q_len),
        ("context", context),
        ("kv_len", kv_len),
        ("owners", owners),
        ("g", g),
        ("dq", dq),
        ("dv", dv),
        ("s2_tile", s2_tile),
    ):
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(f"sparse_mte1_geometry_invalid:{name}")
    if (
        q_len <= 0
        or q_len > MAX_SPARSE_TOKENS
        or kv_len <= 0
        or kv_len > MAX_SPARSE_TOKENS
        or context < 0
        or context > MAX_SPARSE_TOKENS
        or owners <= 0
        or owners > MAX_SPARSE_OWNERS
        or g <= 0
        or g > MAX_SPARSE_OWNERS
        or dq <= 0
        or dq > MAX_SPARSE_DIM
        or dv <= 0
        or dv > MAX_SPARSE_DIM
        or s2_tile <= 0
        or s2_tile > MAX_SPARSE_DIM
    ):
        raise ValueError("sparse_mte1_geometry_invalid")


def sparse_mte1_bytes(
    q_len: int,
    context: int,
    kv_len: int,
    *,
    causal: bool = True,
    owners: int = 32,
    g: int = 64,
    dq: int = 576,
    dv: int = 512,
    s2_tile: int = 128,
) -> dict[str, Any]:
    """Derive exact per-owner QK/PV L1->L0A/B critical bytes in closed form."""
    _validate_geometry_scalars(
        q_len=q_len,
        context=context,
        kv_len=kv_len,
        owners=owners,
        g=g,
        dq=dq,
        dv=dv,
        s2_tile=s2_tile,
    )
    width = -(-q_len // owners)
    aligned_full = ((s2_tile + 15) // 16) * 16
    qk_full = 2 * g * dq + 2 * aligned_full * dq
    pv_full = 2 * g * aligned_full + 2 * dv * aligned_full
    ub_per_tile = 2 * g * s2_tile

    per_owner: list[dict[str, int]] = []
    for start in range(0, q_len, width):
        qk = pv = ub = tiles = 0
        end = min(start + width, q_len)
        for index in range(start, end):
            selected = (
                min(kv_len, context + index + 1) if causal else min(kv_len, context + q_len)
            )
            if selected <= 0:
                continue
            full_tiles, rem_rows = divmod(selected, s2_tile)
            if full_tiles:
                qk += full_tiles * qk_full
                pv += full_tiles * pv_full
            if rem_rows:
                aligned_rem = ((rem_rows + 15) // 16) * 16
                qk += 2 * g * dq + 2 * aligned_rem * dq
                pv += 2 * g * aligned_rem + 2 * dv * aligned_rem
            row_tiles = full_tiles + (1 if rem_rows else 0)
            ub += row_tiles * ub_per_tile
            tiles += row_tiles
        per_owner.append(
            {
                "qk_pv_bytes": qk + pv,
                "qk_bytes": qk,
                "pv_bytes": pv,
                "ub_bytes": ub,
                "tiles": tiles,
            }
        )
    critical_index = max(
        range(len(per_owner)), key=lambda index: per_owner[index]["qk_pv_bytes"]
    )
    critical = per_owner[critical_index]
    return {
        "q_len": q_len,
        "context": context,
        "kv_len": kv_len,
        "causal": bool(causal),
        "owners": owners,
        "g": g,
        "dq": dq,
        "dv": dv,
        "s2_tile": s2_tile,
        "per_owner_width": width,
        "critical_owner_index": critical_index,
        "critical_qk_pv_bytes": critical["qk_pv_bytes"],
        "critical_qk_bytes": critical["qk_bytes"],
        "critical_pv_bytes": critical["pv_bytes"],
        "critical_ub_bytes": critical["ub_bytes"],
        "critical_tiles": critical["tiles"],
        "total_qk_pv_bytes": sum(item["qk_pv_bytes"] for item in per_owner),
        "total_ub_bytes": sum(item["ub_bytes"] for item in per_owner),
        "total_tiles": sum(item["tiles"] for item in per_owner),
    }


def _positional_shapes(value: Any, limit: int = 5) -> tuple[tuple[int, ...] | None, ...]:
    text = str(value or "").strip().strip('"')
    if not text:
        return ()
    slots: list[tuple[int, ...] | None] = []
    for raw in text.split(";")[:limit]:
        cell = raw.strip().strip('"')
        if not cell or cell in {"N/A", "NULL", "None"}:
            slots.append(None)
            continue
        try:
            dims = tuple(int(part.strip()) for part in cell.split(","))
        except ValueError:
            slots.append(())
            continue
        slots.append(dims if dims and all(dim >= 0 for dim in dims) else ())
    return tuple(slots)


def _candidate_geometry_matches(
    candidate: Mapping[str, Any],
    *,
    q_len: int,
    required_kv: int,
    g: int,
    dq: int,
    dv: int,
    s2_tile: int,
    kv_heads: int,
    kv_packed_dim: int,
) -> bool:
    if not candidate.get("tensor_geometry_parsed"):
        return False
    if str(candidate.get("dtype") or "") != "bf16":
        return False
    if str(candidate.get("output_dtype") or "") != "bf16":
        return False
    q_shape = tuple(candidate.get("q_shape") or ())
    out_shape = tuple(candidate.get("out_shape") or ())
    if q_shape != (q_len, g, dq) or out_shape != (q_len, g, dv):
        return False
    k_shape = tuple(candidate.get("k_shape") or ())
    if (
        len(k_shape) != 4
        or k_shape[0] <= 0
        or k_shape[0] * k_shape[1] < required_kv
        or k_shape[1] != s2_tile
        or k_shape[2] != kv_heads
        or k_shape[3] != kv_packed_dim
    ):
        return False
    v_shape = candidate.get("v_shape")
    if v_shape is not None and tuple(v_shape) != k_shape:
        return False
    in_dtypes = candidate.get("input_dtypes_slots") or ()
    if len(in_dtypes) < 2 or in_dtypes[0] != "bf16" or in_dtypes[1] != "fp8_e4m3":
        return False
    if v_shape is not None and (len(in_dtypes) < 3 or in_dtypes[2] != "fp8_e4m3"):
        return False
    index_shape = candidate.get("index_shape")
    if index_shape is not None:
        idx_dims = tuple(index_shape)
        if (
            len(idx_dims) != 3
            or idx_dims[0] != q_len
            or idx_dims[1] != kv_heads
            or idx_dims[2] < required_kv
        ):
            return False
    return True


def _parse_sparse_geometry(sparse_geometry: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(sparse_geometry, Mapping):
        raise ProfilerUsageError("sparse_geometry must be a mapping")
    q_len = _strict_int(sparse_geometry, "q_len")
    context = _strict_int(sparse_geometry, "context", 0)
    kv_len = _strict_int(sparse_geometry, "kv_len", q_len)
    owners = _strict_int(sparse_geometry, "owners", 32)
    mix = _strict_int(sparse_geometry, "mix_block_num", 64)
    g = _strict_int(sparse_geometry, "g", 64)
    dq = _strict_int(sparse_geometry, "dq", 576)
    dv = _strict_int(sparse_geometry, "dv", 512)
    s2_tile = _strict_int(sparse_geometry, "s2_tile", 128)
    kv_heads = _strict_int(sparse_geometry, "kv_heads", 1)
    default_kv_packed_dim = dv + 2 * max(0, dq - dv) + (dv // 32)
    kv_packed_dim = _strict_int(sparse_geometry, "kv_packed_dim", default_kv_packed_dim)
    if (
        mix <= 0
        or mix > MAX_SPARSE_OWNERS
        or kv_heads <= 0
        or kv_heads > MAX_SPARSE_OWNERS
        or kv_packed_dim <= 0
        or kv_packed_dim > MAX_SPARSE_DIM
    ):
        raise ProfilerUsageError("invalid sparse_geometry: mix_block_num/kv dimensions out of range")
    raw_causal = sparse_geometry.get("causal", True)
    if not isinstance(raw_causal, bool):
        raise ProfilerUsageError("sparse_geometry.causal must be a boolean")
    try:
        _validate_geometry_scalars(
            q_len=q_len,
            context=context,
            kv_len=kv_len,
            owners=owners,
            g=g,
            dq=dq,
            dv=dv,
            s2_tile=s2_tile,
        )
    except ValueError as exc:
        raise ProfilerUsageError(f"invalid sparse_geometry: {exc}") from exc
    return {
        "q_len": q_len,
        "context": context,
        "kv_len": kv_len,
        "required_kv": min(kv_len, context + q_len),
        "owners": owners,
        "mix": mix,
        "g": g,
        "dq": dq,
        "dv": dv,
        "s2_tile": s2_tile,
        "kv_heads": kv_heads,
        "kv_packed_dim": kv_packed_dim,
        "causal": raw_causal,
        "state": str(sparse_geometry.get("op_state", "dynamic")).lower(),
        "phase": str(sparse_geometry.get("phase", "prefill")).lower(),
    }


class SparseSupplyAccumulator:
    """Bounded O(1)-when-inactive collector that filters before retaining samples."""

    _MAX_DEDUP_EVENTS = 1_000_000

    def __init__(
        self,
        *,
        sparse_geometry: Mapping[str, Any] | None = None,
        enabled: bool | None = None,
        max_groups: int = MAX_SPARSE_GROUPS,
        max_samples: int = MAX_SPARSE_SAMPLES,
    ) -> None:
        self.spec = _parse_sparse_geometry(sparse_geometry) if sparse_geometry is not None else None
        self.enabled = (self.spec is not None) if enabled is None else bool(enabled and self.spec)
        self.max_groups = max(1, int(max_groups))
        self.max_samples = max(1, int(max_samples))
        self.grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        self.group_totals: dict[tuple[Any, ...], int] = {}
        self._seen_events: set[tuple[str, ...]] = set()
        self._phys_to_dedup: dict[tuple[str, str, str], tuple[str, ...]] = {}
        self.capped_samples = 0
        self.dropped_groups = 0
        self.geometry_mismatch = 0
        self.dedup_budget_reached = False

    def add_candidate(
        self,
        candidate: Mapping[str, Any],
        *,
        retain: bool = True,
        phys_key: tuple[str, str, str] | None = None,
    ) -> None:
        if not self.enabled or self.spec is None:
            return
        spec = self.spec
        if str(candidate.get("native_type")) != SPARSE_NATIVE_TYPE:
            return
        if int(candidate.get("q_tokens") or -1) != spec["q_len"]:
            return
        if int(candidate.get("block_num") or -1) != spec["owners"]:
            return
        if int(candidate.get("mix_block_num") or -1) != spec["mix"]:
            return
        if str(candidate.get("op_state") or "").lower() != spec["state"]:
            return
        if not candidate.get("mte1_us") or not candidate.get("elapsed_us"):
            return
        raw_eid = candidate.get("event_id")
        raw_ridx = candidate.get("row_index")
        event_token = (
            str(raw_eid)
            if raw_eid not in (None, "")
            else (f"row:{raw_ridx}" if raw_ridx is not None else None)
        )
        if event_token is not None:
            dedup_key = (
                str(candidate.get("rank_id") or ""),
                str(candidate.get("device_id") or ""),
                str(candidate.get("source") or ""),
                str(candidate.get("source_sha256") or ""),
                event_token,
            )
            if dedup_key in self._seen_events:
                return
            if retain:
                if len(self._seen_events) < self._MAX_DEDUP_EVENTS:
                    self._seen_events.add(dedup_key)
                    if phys_key is not None:
                        self._phys_to_dedup[phys_key] = dedup_key
                else:
                    self.dedup_budget_reached = True
        if not _candidate_geometry_matches(
            candidate,
            q_len=spec["q_len"],
            required_kv=spec["required_kv"],
            g=spec["g"],
            dq=spec["dq"],
            dv=spec["dv"],
            s2_tile=spec["s2_tile"],
            kv_heads=spec["kv_heads"],
            kv_packed_dim=spec["kv_packed_dim"],
        ):
            self.geometry_mismatch += 1
            return
        placement_key = (
            spec["q_len"],
            spec["owners"],
            spec["mix"],
            spec["state"],
            str(candidate.get("rank_id") or ""),
            str(candidate.get("device_id") or ""),
            str(candidate.get("source") or ""),
            str(candidate.get("source_sha256") or ""),
        )
        bucket = self.grouped.get(placement_key)
        if bucket is None:
            if len(self.grouped) >= self.max_groups:
                self.dropped_groups += 1
                return
            self.grouped[placement_key] = [dict(candidate)]
            self.group_totals[placement_key] = 1
            return
        self.group_totals[placement_key] = self.group_totals.get(placement_key, len(bucket)) + 1
        if len(bucket) >= self.max_samples:
            self.capped_samples += 1
            return
        bucket.append(dict(candidate))

    def add_event(
        self, observation: Observation, event: Event, *, retain: bool = True
    ) -> None:
        if not self.enabled:
            return
        cand = sparse_supply_candidate(observation, event)
        if cand is not None:
            phys_key = (str(observation.rank_id), str(observation.source.path), str(event.event_id))
            self.add_candidate(cand, retain=retain, phys_key=phys_key)

    def evict_physical_key(self, phys_key: tuple[str, str, str]) -> None:
        if (dkey := self._phys_to_dedup.pop(phys_key, None)) is not None:
            self._seen_events.discard(dkey)


def summarize_sparse_mte1(
    candidates: SparseSupplyAccumulator | Iterable[Mapping[str, Any]],
    *,
    source_identity: Mapping[str, Any] | None,
    sparse_geometry: Mapping[str, Any] | None,
    hardware: str | None = None,
    limitations: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Derive scoped saturated MTE1 resource services with bounded sample retention."""
    if sparse_geometry is None:
        return []
    spec = _parse_sparse_geometry(sparse_geometry)
    q_len = spec["q_len"]
    context = spec["context"]
    kv_len = spec["kv_len"]
    owners = spec["owners"]
    mix = spec["mix"]
    g = spec["g"]
    dq = spec["dq"]
    dv = spec["dv"]
    s2_tile = spec["s2_tile"]
    kv_heads = spec["kv_heads"]
    kv_packed_dim = spec["kv_packed_dim"]
    causal = spec["causal"]
    state = spec["state"]
    phase = spec["phase"]
    if (
        not source_identity
        or source_identity.get("source_scope") != "r64"
        or source_identity.get("image_digest") != R64_IMAGE_SHA
    ):
        if limitations is not None:
            limitations.append(
                {
                    "code": "sparse_mte1_source_not_r64",
                    "detail": (
                        "sparse_geometry was supplied, but capture deployment source is not "
                        "certified R64; no sparse MTE1 resource service was emitted"
                    ),
                    "severity": "medium",
                }
            )
        return []
    if state != "dynamic" or phase != "prefill":
        if limitations is not None:
            limitations.append(
                {
                    "code": "sparse_mte1_not_prefill_dynamic",
                    "detail": (
                        f"sparse_geometry declared phase={phase!r}, op_state={state!r}; "
                        "saturated sparse MTE1 service requires prefill/dynamic"
                    ),
                    "severity": "medium",
                }
            )
        return []

    if isinstance(candidates, SparseSupplyAccumulator) and candidates.spec == spec:
        acc = candidates
    else:
        acc = SparseSupplyAccumulator(sparse_geometry=sparse_geometry)
        raw_iter = (
            (item for rows in candidates.grouped.values() for item in rows)
            if isinstance(candidates, SparseSupplyAccumulator)
            else candidates
        )
        for item in raw_iter:
            acc.add_candidate(item)

    grouped = acc.grouped
    capped = acc.capped_samples
    geometry_mismatch = acc.geometry_mismatch
    if acc.dedup_budget_reached and limitations is not None:
        limitations.append({
            "code": "sparse_mte1_dedup_budget_reached",
            "detail": f"sparse PMU overlap deduplication reached {acc._MAX_DEDUP_EVENTS} active events",
            "severity": "medium",
        })
    if acc.dropped_groups and limitations is not None:
        limitations.append(
            {
                "code": "sparse_mte1_groups_capped",
                "detail": (
                    f"{acc.dropped_groups} sparse placement group(s) exceeded the "
                    f"{acc.max_groups}-group retention cap"
                ),
                "severity": "low",
            }
        )

    if capped and limitations is not None:
        limitations.append(
            {
                "code": "sparse_mte1_samples_capped",
                "detail": (
                    f"{capped} KvQuantSparseFlashAttention samples exceeded the "
                    f"{MAX_SPARSE_SAMPLES}-sample retention cap"
                ),
                "severity": "low",
            }
        )
    if not grouped:
        if limitations is not None:
            if geometry_mismatch:
                limitations.append(
                    {
                        "code": "sparse_mte1_tensor_geometry_mismatch",
                        "detail": (
                            f"{geometry_mismatch} KvQuantSparseFlashAttention event(s) matched "
                            f"q_len={q_len}, owners={owners}, mix_block_num={mix}, op_state={state!r} "
                            f"but disagreed with declared Q/KV/output tensor geometry "
                            f"(g={g}, dq={dq}, dv={dv}, s2_tile={s2_tile}, bf16->bf16)"
                        ),
                        "severity": "high",
                    }
                )
            else:
                limitations.append(
                    {
                        "code": "sparse_mte1_no_matching_events",
                        "detail": (
                            "no complete KvQuantSparseFlashAttention PMU event matched the declared "
                            "sparse_geometry (q_len/owners/mix_block_num/op_state/bf16)"
                        ),
                        "severity": "medium",
                    }
                )
        return []

    geometry = sparse_mte1_bytes(
        q_len,
        context,
        kv_len,
        causal=causal,
        owners=owners,
        g=g,
        dq=dq,
        dv=dv,
        s2_tile=s2_tile,
    )
    records: list[dict[str, Any]] = []
    for rows in grouped.values():
        mte1 = statistics.median(float(item["mte1_us"]) for item in rows)
        elapsed = statistics.median(float(item["elapsed_us"]) for item in rows)
        if mte1 <= 0:
            continue
        rate = geometry["critical_qk_pv_bytes"] / (mte1 * 1e-6)
        first = rows[0]
        rank_id = first.get("rank_id") or None
        rank_index = first.get("rank_index")
        device_id = first.get("device_id") if first.get("device_id") not in (None, "") else None
        records.append(
            {
                "schema_version": RESOURCE_SERVICE_SCHEMA,
                "resource": "mte1",
                "native_type": SPARSE_NATIVE_TYPE,
                "kernel": SPARSE_NATIVE_TYPE,
                "source_identity": dict(source_identity),
                "hardware": str(hardware or sparse_geometry.get("hardware") or ""),
                "rank_id": rank_id,
                "rank_index": rank_index,
                "device_id": device_id,
                "dtype": "bf16",
                "layout": str(sparse_geometry.get("layout") or "QK/PV BF16 L1->L0A/L0B"),
                "input_formats": first.get("input_formats"),
                "output_formats": first.get("output_formats"),
                "phase": phase,
                "op_state": state,
                "scope": "critical_owner",
                "shape_class": str(
                    sparse_geometry.get("shape_class")
                    or f"prefill_causal_q{q_len}_g{geometry['g']}_"
                    f"dq{geometry['dq']}_dv{geometry['dv']}_s2tile{geometry['s2_tile']}"
                ),
                "geometry_binding": {
                    **dict(sparse_geometry),
                    "q_len": q_len,
                    "context": context,
                    "kv_len": kv_len,
                    "owners": owners,
                    "mix_block_num": mix,
                    "g": g,
                    "dq": dq,
                    "dv": dv,
                    "s2_tile": s2_tile,
                    "kv_heads": kv_heads,
                    "kv_packed_dim": kv_packed_dim,
                    "causal": causal,
                    "op_state": state,
                    "phase": phase,
                },
                "owners": owners,
                "block_num": owners,
                "mix_block_num": mix,
                "measured_q_tokens": q_len,
                "measured_context": context,
                "measured_kv_len": kv_len,
                "measured_critical_bytes": geometry["critical_qk_pv_bytes"],
                "measured_total_bytes": geometry["total_qk_pv_bytes"],
                "measured_critical_ub_bytes": geometry["critical_ub_bytes"],
                "measured_total_ub_bytes": geometry["total_ub_bytes"],
                "critical_owner_index": geometry["critical_owner_index"],
                "event_count": len(rows),
                "median_mte1_us": mte1,
                "median_elapsed_us": elapsed,
                "rate_bytes_per_s": rate,
                "pmu": "aic_mte1_time",
                "source": first.get("source"),
                "source_sha256": first.get("source_sha256"),
                "provenance": {
                    "rank_id": rank_id,
                    "rank_index": rank_index,
                    "device_id": device_id,
                    "source": first.get("source"),
                    "event_ids": [item.get("event_id") for item in rows[:8]],
                    "row_indices": [item.get("row_index") for item in rows[:8]],
                    "source_sha256": first.get("source_sha256"),
                    "geometry_basis": sparse_geometry.get("geometry_basis"),
                    "not_elapsed_rate": True,
                    "not_index_or_routing_target": True,
                },
            }
        )
    return records


def sparse_supply_candidate(observation: Observation, event: Event) -> dict[str, Any] | None:
    op_type = str(event.op_type or "").strip()
    op_name = str(event.name or "").strip()
    if op_type:
        if op_type != SPARSE_NATIVE_TYPE:
            return None
        if op_name and op_name != SPARSE_NATIVE_TYPE and not op_name.startswith(
            f"{SPARSE_NATIVE_TYPE}_"
        ):
            return None
    elif op_name != SPARSE_NATIVE_TYPE:
        return None
    if not event.complete_in(observation.window.start_ns, observation.window.end_ns):
        return None
    in_slots = _positional_shapes(event.input_shapes, limit=5)
    out_slots = _positional_shapes(event.output_shapes, limit=2)
    q_shape = in_slots[0] if in_slots and in_slots[0] else ()
    k_shape = in_slots[1] if len(in_slots) >= 2 and in_slots[1] is not None else ()
    v_shape = in_slots[2] if len(in_slots) >= 3 else None
    index_shape = in_slots[3] if len(in_slots) >= 4 else None
    out_shape = out_slots[0] if out_slots and out_slots[0] else ()
    q_tokens = int(q_shape[0]) if len(q_shape) >= 1 else 0
    in_dtypes = _dtype_slots(event.input_dtypes, limit=5)
    out_dtypes = _dtype_slots(event.output_dtypes, limit=2)
    pmu = event.pmu_map()
    mte1_ns = pmu.get("aic_mte1_time")
    return {
        "native_type": SPARSE_NATIVE_TYPE,
        "rank_id": event.rank_id or observation.rank_id,
        "rank_index": (
            event.rank_index if event.rank_index is not None else observation.rank_index
        ),
        "device_id": event.device_id,
        "q_tokens": q_tokens,
        "q_shape": q_shape,
        "k_shape": k_shape,
        "v_shape": v_shape,
        "index_shape": index_shape,
        "out_shape": out_shape,
        "input_dtypes_slots": in_dtypes,
        "tensor_geometry_parsed": True,
        "dtype": (in_dtypes[0] or "") if in_dtypes else "",
        "output_dtype": (out_dtypes[0] or "") if out_dtypes else "",
        "block_num": event.block_dim,
        "mix_block_num": event.mix_block_dim,
        "op_state": event.op_state,
        "input_formats": event.input_formats,
        "output_formats": event.output_formats,
        "mte1_us": (mte1_ns / 1000.0) if mte1_ns and mte1_ns > 0 else None,
        "elapsed_us": (event.duration_ns / 1000.0) if event.duration_ns else None,
        "source": observation.source.path,
        "source_sha256": observation.source.sha256,
        "event_id": event.event_id,
        "row_index": event.locator.get("row_index"),
    }


def build_measured_supply_summary(
    supply_candidates: MatrixSupplyAccumulator | Iterable[Mapping[str, Any]],
    sparse_candidates: SparseSupplyAccumulator | Iterable[Mapping[str, Any]],
    *,
    physical_owners: int | None = None,
    source_identity: Mapping[str, Any] | None = None,
    sparse_geometry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize both matrix dual-load supply and optional sparse MTE1 service."""
    sparse_limitations: list[dict[str, Any]] = []
    if sparse_geometry is not None and not isinstance(sparse_geometry, Mapping):
        raise ProfilerUsageError("sparse_geometry must be a mapping")
    hardware = (
        sparse_geometry.get("hardware") if isinstance(sparse_geometry, Mapping) else None
    )
    resource_services = summarize_sparse_mte1(
        sparse_candidates,
        source_identity=source_identity,
        sparse_geometry=sparse_geometry,
        hardware=hardware,
        limitations=sparse_limitations,
    )
    return summarize_measured_supply(
        supply_candidates,
        physical_owners=physical_owners,
        source_identity=source_identity,
        resource_services=resource_services,
        extra_limitations=sparse_limitations,
        saturation_threshold=SATURATION_THRESHOLD,
    )


__all__ = [
    "MAX_SPARSE_SAMPLES",
    "MAX_SPARSE_TOKENS",
    "RESOURCE_SERVICE_SCHEMA",
    "SPARSE_NATIVE_TYPE",
    "SparseSupplyAccumulator",
    "build_measured_supply_summary",
    "sparse_mte1_bytes",
    "sparse_supply_candidate",
    "summarize_sparse_mte1",
]
