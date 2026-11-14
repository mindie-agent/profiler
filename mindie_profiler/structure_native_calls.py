"""BIND1 native-call correspondence, raw HCCL alias deduplication, and graph seal check.

[Role]
  Resolve declared ``mindie-sim`` native-call bindings (``BIND1``) and signed
  rank-local HCCL raw task aliases during ``StructureMapper`` window scans
  without conflating name/shape correspondence with occurrence proof.

[Invariants]
  * ``verify_graph_id`` accepts both the current ``mindie-sim`` seal (which
    excludes derived ``native_calls`` and ``native_call_coverage`` alongside
    ``graph_id``/``source``) and the historical seal.
  * Declared native-call entry/kernel names correspond only when the captured
    tensor signature agrees with ``typed``; ``occurrence_binding_implied`` and
    ``observed_proof`` remain ``False`` for signature-only correspondence.
  * Raw relational identity (``rank_id``, ``global_task_id``, ``stream_id``,
    ``task_id``, ``connection_id``, ``device_id``, ``start_ns``, ``end_ns``) is
    tracked across all examined window events (never truncated by
    ``mapping_limit``) and deduplicated via true interval union.

[Timeouts & Locks]
  Pure in-memory per-window tracking bounded by ``max_events``; no I/O or locks.

[Side-Effect Policy]
  Mutates only the mapper-owned cache and retained sample rows for the active
  mapping pass; no external side effects.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from .accounting import merge_intervals
from .events import Event, ProfilerUsageError
from .structure_native_signature import (
    event_signature,
    native_call_signature_match,
    parse_paired_lanes,
)


def _union_ns(intervals: list[tuple[int, int]]) -> int:
    return sum(right - left for left, right in merge_intervals(intervals))


def _seal_digest(payload: Mapping[str, Any]) -> str:
    digest = sha256()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(payload):
        digest.update(chunk.encode("utf-8"))
    return "sha256:" + digest.hexdigest()


def verify_graph_id(structure: Mapping[str, Any]) -> str:
    declared = structure.get("graph_id")
    current = _seal_digest(
        {
            key: value
            for key, value in structure.items()
            if key not in {"graph_id", "source", "native_calls", "native_call_coverage"}
        }
    )
    if declared == current:
        return current
    legacy = _seal_digest(
        {key: value for key, value in structure.items() if key not in {"graph_id", "source"}}
    )
    if declared == legacy:
        return legacy
    raise ProfilerUsageError(
        "structure graph_id does not match its contents; re-export the structure"
    )


def event_raw_identity(event: Event) -> tuple[str, ...] | None:
    """Signed raw task identity used for one HCCL call's rank-local aliases."""
    locator = event.locator or {}
    join_status = str(locator.get("task_join_status") or "")
    if join_status.startswith("unresolved"):
        return None
    global_task = locator.get(
        "global_task_id", locator.get("globalTaskId", locator.get("task_global_id"))
    )
    connection = locator.get("connection_id", locator.get("connectionId"))
    if global_task in (None, "") or connection in (None, ""):
        return None
    if event.stream_id == "" or event.task_id == "":
        return None
    return (
        str(event.rank_id),
        str(global_task),
        str(event.stream_id),
        str(event.task_id),
        str(connection),
        str(event.device_id),
        str(event.start_ns),
        str(event.end_ns),
    )


def _comm_op_token(event: Event) -> tuple[Any, ...] | None:
    if event.table != "COMMUNICATION_OP":
        return None
    locator = event.locator or {}
    op_id = locator.get("op_id", locator.get("opId"))
    rowid = locator.get("rowid")
    if op_id not in (None, ""):
        return ("op_id", str(op_id))
    if rowid not in (None, ""):
        return ("rowid", str(rowid))
    return ("event_id", event.event_id)


def conflicted_comm_raw_identities(events: Any) -> set[tuple[str, ...]]:
    """Return raw task identities claimed by multiple distinct COMMUNICATION_OP rows."""
    owners: dict[tuple[str, ...], tuple[Any, ...]] = {}
    conflicted: set[tuple[str, ...]] = set()
    for event in events:
        if (token := _comm_op_token(event)) is None:
            continue
        if (raw := event_raw_identity(event)) is None or raw in conflicted:
            continue
        prev = owners.get(raw)
        if prev is not None and prev != token:
            conflicted.add(raw)
        else:
            owners[raw] = token
    return conflicted


_MAX_IMPLEMENTATION_CACHE = 4096


def resolve_implementation_correspondence(
    cache: dict[tuple[Any, ...], dict[str, Any] | None],
    target_index: Any,
    rank_candidates_fn: Callable[[Any, str], list[str]],
    kind: str,
    rank: str,
    event: Event | None = None,
    *,
    target_registry: dict[int, tuple[str, ...]] | None = None,
    conflicted_raws: set[tuple[str, ...]] | None = None,
) -> dict[str, Any] | None:
    signature = event_signature(event) if event is not None else None
    raw = event_raw_identity(event) if event is not None else None
    is_conflicted_raw = bool(
        raw is not None and conflicted_raws is not None and raw in conflicted_raws
    )
    matched_raw = (
        raw
        if (raw is not None and not is_conflicted_raw and raw in target_index.native_call_observed)
        else None
    )
    alt_name = event.name if (event is not None and event.name and event.name != kind) else None
    event_match_key = (
        None
        if event is None
        else (
            parse_paired_lanes(event.input_shapes, event.input_dtypes, event.input_formats),
            parse_paired_lanes(event.output_shapes, event.output_dtypes, event.output_formats),
        )
    )
    cache_key = (
        kind,
        alt_name,
        rank,
        event_match_key,
        matched_raw,
    )
    if cache_key in cache:
        return cache[cache_key]

    targets: list[str] = []
    basis = "declared_native_implementation"
    signature_match: bool | None = None
    matched_label = kind

    if matched_raw is not None:
        alias_targets = list(
            dict.fromkeys(
                rank_candidates_fn(target_index.native_call_observed.get(matched_raw, ()), rank)
            )
        )
        alias_bindings = [
            target_index.native_bindings[key]
            for key in alias_targets
            if key in target_index.native_bindings
        ]
        alias_call_ids = {row.get("call_id") for row in alias_bindings if row.get("call_id")}
        alias_owners = {
            (
                str(target_index.all.get(key, {}).get("replica")),
                str(target_index.all.get(key, {}).get("stage")),
                (target_index.native_bindings[key].get("timing_owner") or {}).get("op_id")
                or target_index.native_bindings[key].get("op_id")
                or key,
            )
            for key in alias_targets
            if key in target_index.native_bindings
        }
        if (
            alias_targets
            and len(alias_bindings) == len(alias_targets)
            and len(alias_call_ids) == 1
            and len(alias_owners) == 1
        ):
            targets = alias_targets
            basis = "observed_hccl_alias_same_call"
            signature_match = True

    impl_targets = (
        list(
            dict.fromkeys(
                rank_candidates_fn(target_index.native_implementations.get(kind, ()), rank)
            )
        )
        if not targets
        else []
    )
    bound_verdicts: list[tuple[str, bool | None]] = []
    if impl_targets and event is not None:
        bound_verdicts = [
            (node, native_call_signature_match(target_index.native_bindings[node], event))
            for node in impl_targets
            if node in target_index.native_bindings
        ]
        matched_impl = [node for node, verdict in bound_verdicts if verdict is True]
        if matched_impl:
            targets = matched_impl
            signature_match = True
            basis = "declared_native_call_signature"

    if not targets:
        names = (kind,) if alt_name is None else (kind, alt_name)
        for candidate_name in names:
            raw_candidates = list(
                dict.fromkeys(
                    [
                        *target_index.native_call_entries.get(candidate_name, ()),
                        *target_index.native_call_kernels.get(candidate_name, ()),
                    ]
                )
            )
            candidates = rank_candidates_fn(raw_candidates, rank)
            if not candidates:
                continue
            if event is not None:
                matched = [
                    node
                    for node in candidates
                    if native_call_signature_match(target_index.native_bindings[node], event)
                    is True
                ]
                if matched:
                    targets = matched
                    signature_match = True
                    matched_label = candidate_name
                    basis = "declared_native_call_signature"
                    break
            elif not impl_targets:
                targets = candidates
                matched_label = candidate_name
                basis = "declared_native_call_no_event"
                break

    if not targets and impl_targets:
        targets = impl_targets
        basis = "declared_native_implementation"
        if bound_verdicts:
            verdict_set = {verdict for _, verdict in bound_verdicts}
            if False in verdict_set and None not in verdict_set:
                signature_match = False

    if targets:
        description = target_index.describe_implementation(matched_label, targets)
        if (
            event is not None
            and basis == "declared_native_implementation"
            and signature_match is not True
        ):
            description["native_call"] = None
        observed_alias = (
            basis == "observed_hccl_alias_same_call"
            and description.get("native_call") is not None
            and bool((description["native_call"].get("timing_owner") or {}).get("op_id"))
        )
        description.update(
            basis=basis,
            rank=rank,
            observed_signature=(
                {
                    "shapes": [list(shape) for shape in signature[0]],
                    "dtypes": list(signature[1]),
                }
                if signature is not None
                else None
            ),
            raw_identity=(
                {
                    "rank_id": matched_raw[0],
                    "global_task_id": matched_raw[1],
                    "stream_id": matched_raw[2],
                    "task_id": matched_raw[3],
                    "connection_id": matched_raw[4],
                    "device_id": matched_raw[5],
                    "start_ns": matched_raw[6],
                    "end_ns": matched_raw[7],
                }
                if observed_alias and matched_raw is not None
                else None
            ),
            signature_match=signature_match,
            observed_proof=observed_alias,
            prepare_only_control=not observed_alias,
            occurrence_binding_implied=observed_alias,
        )
        call = description.get("native_call") or {}
        if call.get("call_id"):
            description["call_ids"] = [call["call_id"]]
        if target_registry is not None:
            target_registry[id(description)] = tuple(targets)
    else:
        description = None

    if len(cache) >= _MAX_IMPLEMENTATION_CACHE:
        cache.clear()
        if target_registry is not None:
            target_registry.clear()
            if description is not None:
                target_registry[id(description)] = tuple(targets)
    cache[cache_key] = description
    return description


class OperatorCorrespondenceAccumulator:
    """Order-independent per-operator correspondence aggregator within one window."""

    def __init__(self) -> None:
        self._variants: dict[str, dict[str, Any]] = {}
        self._counts: Counter[str] = Counter()
        self._target_set: set[str] = set()
        self._none_count = 0

    def add(
        self,
        correspondence: Mapping[str, Any] | None,
        targets: tuple[str, ...] | None = None,
    ) -> None:
        if correspondence is None:
            self._none_count += 1
            return
        canon = json.dumps(correspondence, sort_keys=True, separators=(",", ":"))
        if canon not in self._variants:
            self._variants[canon] = dict(correspondence)
        self._counts[canon] += 1
        if targets is not None:
            self._target_set.update(targets)
        else:
            self._target_set.update(correspondence.get("declared_node_ids") or ())
            self._target_set.update(correspondence.get("declared_subgraph_ids") or ())

    def finish(self, op_type: str, rank: str, target_index: Any) -> dict[str, Any] | None:
        if not self._variants:
            return None
        if len(self._variants) == 1 and self._none_count == 0:
            return dict(next(iter(self._variants.values())))
        ordered = sorted(self._variants.items(), key=lambda item: item[0])
        union_targets = [key for key in target_index.all if key in self._target_set]
        summary = target_index.describe_implementation(op_type, union_targets)
        call_ids = sorted(
            {str(cid) for _, corr in ordered for cid in (corr.get("call_ids") or ()) if cid}
        )
        verdicts = {corr.get("signature_match") for _, corr in ordered}
        if self._none_count > 0:
            verdicts.add(None)
        sig_match: bool | None = (
            True if verdicts == {True} else False if verdicts == {False} else None
        )
        all_observed = self._none_count == 0 and all(
            bool(corr.get("observed_proof")) for _, corr in ordered
        )
        single_call = (
            summary.get("native_call")
            if (self._none_count == 0 and len(call_ids) == 1 and sig_match is True)
            else None
        )
        summary.update(
            basis="multiple_event_correspondences",
            rank=rank,
            native_call=single_call,
            observed_signature=None,
            raw_identity=None,
            signature_match=sig_match,
            observed_proof=all_observed,
            prepare_only_control=not all_observed,
            occurrence_binding_implied=bool(all_observed and single_call is not None),
            variant_count=len(ordered) + (1 if self._none_count > 0 else 0),
            unmatched_event_count=self._none_count,
            variants=[
                {**corr, "event_count": self._counts[canon]} for canon, corr in ordered[:64]
            ],
        )
        if call_ids:
            summary["call_ids"] = call_ids
        return summary


class NativeCallGlobalTracker:
    """Bounded cross-window tracker retaining unclosed spanning raw identities."""

    def __init__(self, *, max_active: int = 100_000) -> None:
        if max_active <= 0:
            raise ProfilerUsageError("max_active must be positive")
        self.max_active = int(max_active)
        self.primary_by_raw: dict[tuple[str, ...], str] = {}
        self.presentation_counts: Counter[tuple[str, ...]] = Counter()
        self.identity_counts: Counter[str] = Counter()
        self.comm_owner_by_raw: dict[tuple[str, ...], tuple[Any, ...]] = {}
        self.conflicted_raws: set[tuple[str, ...]] = set()

    def evict_closed(self, window_end_ns: int | None, rank_id: str | None = None) -> None:
        if window_end_ns is None:
            return
        rank_text = str(rank_id) if rank_id is not None else None
        candidates = set(self.primary_by_raw) | set(self.comm_owner_by_raw) | self.conflicted_raws
        expired = [
            raw
            for raw in candidates
            if (rank_text is None or raw[0] == rank_text) and int(raw[7]) <= window_end_ns
        ]
        for raw in expired:
            self.primary_by_raw.pop(raw, None)
            self.presentation_counts.pop(raw, None)
            self.comm_owner_by_raw.pop(raw, None)
            self.conflicted_raws.discard(raw)


class NativeCallWindowTracker:
    """Full-window native-call occurrence tracker independent of mapping_limit."""

    def __init__(self, global_tracker: NativeCallGlobalTracker, alias_names: set[str]) -> None:
        self._global = global_tracker
        self._alias_names = alias_names
        self._groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)

    def observe(
        self,
        event: Event,
        interval: tuple[int, int],
        correspondence: Mapping[str, Any] | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        raw = event_raw_identity(event)
        comm_token = _comm_op_token(event)
        if raw is not None and comm_token is not None:
            prev_owner = self._global.comm_owner_by_raw.get(raw)
            if raw in self._global.conflicted_raws or (
                prev_owner is not None and prev_owner != comm_token
            ):
                self._global.conflicted_raws.add(raw)
                self._global.comm_owner_by_raw.pop(raw, None)
                self._global.primary_by_raw.pop(raw, None)
                self._global.presentation_counts.pop(raw, None)
                removed = self._groups.pop(raw, ())
                for prior in removed:
                    self._global.identity_counts["observed_raw_identity"] -= 1
                    if self._global.identity_counts["observed_raw_identity"] <= 0:
                        self._global.identity_counts.pop("observed_raw_identity", None)
                    self._global.identity_counts["conflicted_comm_op_claim"] += 1
                    if (sref := prior.get("sample_row")) is not None:
                        sref["native_call_identity"] = "conflicted_comm_op_claim"
                        sref["native_call_occurrence"] = None
            else:
                if (
                    raw not in self._global.comm_owner_by_raw
                    and len(self._global.comm_owner_by_raw) >= self._global.max_active
                ):
                    raise ProfilerUsageError(
                        f"active spanning native-call identities exceeded max_active={self._global.max_active}; "
                        "select narrower rank scopes or raise --max-mapping-events"
                    )
                self._global.comm_owner_by_raw[raw] = comm_token

        if raw is not None and raw in self._global.conflicted_raws:
            if (
                event.table == "COMMUNICATION_OP"
                or event.op_type in self._alias_names
                or event.name in self._alias_names
            ):
                self._global.identity_counts["conflicted_comm_op_claim"] += 1
                return "conflicted_comm_op_claim", None
            return None, None

        native_identity: str | None = None
        if correspondence is not None and correspondence.get("basis") == "observed_hccl_alias_same_call":
            native_identity = "observed_raw_identity"
        elif raw is None and (
            event.op_type in self._alias_names or event.name in self._alias_names
        ):
            native_identity = "unresolved_alias_without_relational_keys"

        if native_identity is not None:
            self._global.identity_counts[native_identity] += 1

        if (
            correspondence is None
            or correspondence.get("basis") != "observed_hccl_alias_same_call"
            or raw is None
        ):
            return native_identity, None

        if (
            raw not in self._global.primary_by_raw
            and len(self._global.primary_by_raw) >= self._global.max_active
        ):
            raise ProfilerUsageError(
                f"active spanning native-call identities exceeded max_active={self._global.max_active}; "
                "select narrower rank scopes or raise --max-mapping-events"
            )
        call = correspondence.get("native_call") or {}
        presentation_id = f"{event.event_id}:{event.op_type}"
        primary = self._global.primary_by_raw.setdefault(raw, presentation_id)
        self._global.presentation_counts[raw] += 1
        index = self._global.presentation_counts[raw]
        occurrence: dict[str, Any] = {
            "call_id": call.get("call_id"),
            "raw_identity": dict(correspondence.get("raw_identity") or {}),
            "charge": "call",
            "call_owner": (call.get("timing_owner") or {}).get("op_id"),
            "primary_presentation": primary,
            "alias_of": None if presentation_id == primary else primary,
            "presentation_id": presentation_id,
            "presentation_index": index,
            "occurrence_key": list(raw),
        }
        self._groups[raw].append(
            {
                "event_id": event.event_id,
                "interval": interval,
                "occurrence": occurrence,
                "sample_row": None,
            }
        )
        return native_identity, occurrence

    def bind_sample_row(self, event: Event, sample_row: dict[str, Any]) -> None:
        raw = event_raw_identity(event)
        if raw is not None and (entries := self._groups.get(raw)):
            entries[-1]["sample_row"] = sample_row

    def finish(
        self,
        *,
        window_end_ns: int | None = None,
        rank_id: str | None = None,
    ) -> list[dict[str, Any]]:
        native_calls: list[dict[str, Any]] = []
        for raw, entries in self._groups.items():
            if raw in self._global.conflicted_raws:
                continue
            presentations = [entry["occurrence"]["presentation_id"] for entry in entries]
            for entry in entries:
                entry["occurrence"].update(
                    presentations=presentations,
                    presentation_count=len(presentations),
                )
            first_occ = entries[0]["occurrence"]
            intervals = [entry["interval"] for entry in entries]
            native_calls.append(
                {
                    "call_id": first_occ.get("call_id"),
                    "rank_id": raw[0],
                    "raw_identity": first_occ.get("raw_identity"),
                    "charge": "call",
                    "call_owner": first_occ.get("call_owner"),
                    "presentation_count": len(presentations),
                    "presentations": presentations,
                    "representative_event_id": entries[0]["event_id"],
                    "activity_ns": _union_ns(intervals),
                    "accounting_basis": "one_call_alias_union_not_sum_of_presentations",
                }
            )
        self._global.evict_closed(window_end_ns, rank_id)
        return native_calls


__all__ = [
    "NativeCallGlobalTracker",
    "NativeCallWindowTracker",
    "OperatorCorrespondenceAccumulator",
    "conflicted_comm_raw_identities",
    "event_raw_identity",
    "event_signature",
    "native_call_signature_match",
    "parse_paired_lanes",
    "resolve_implementation_correspondence",
    "verify_graph_id",
]
