"""Name the fleet reducer from the producer, before any target number.

An explicit mean, median, or sum token stays exact. A declared geometry
population uses the largest complete forward count and the mean. A prefill
body receipt is ``dsh_scoped_prefill.score_prefill_capture`` and sums every
declared window. Phase text alone names neither sum nor mean. B1 is the
historic capture-root proof on one device, not a frame ``sequences_per_replica``
and not a forecast field.
"""
from __future__ import annotations

import functools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from hf_sample_scoring import observed_sample_table

_PREFILL_PRODUCER = "dsh_scoped_prefill.score_prefill_capture"


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _same_number(left: Any, right: Any) -> bool:
    a, b = _finite(left), _finite(right)
    if a is None or b is None:
        return False
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


def _window(observation: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(observation, Mapping):
        return {}
    window = (observation.get("measurements") or {}).get("per_forward_window")
    return window if isinstance(window, Mapping) else {}


def _explicit_reducer(basis: str, row: Mapping[str, Any]) -> str | None:
    """Named aggregate only. An elapsed window is the sample, not the reducer."""
    text = basis.lower()
    if "p50" in text or "median" in text:
        return "median"
    if "sum" in text or "body_span_sum" in text:
        return "sum"
    if "mean" in text:
        return "mean"
    if _finite(row.get("body_span_sum_ms")) is not None:
        return "sum"
    return None


def _frame_records(observation: Mapping[str, Any] | None, values: Sequence[float]) -> list[dict[str, Any]]:
    window = _window(observation)
    table = observed_sample_table(observation, "per_forward_window")
    if table.get("status") == "measured" and len(table.get("keys") or []) == len(values):
        keys = [str(key) for key in table["keys"]]
    else:
        sample_keys = window.get("sample_keys") or window.get("keys") or window.get("labels")
        if (isinstance(sample_keys, Sequence) and not isinstance(sample_keys, (str, bytes))
                and len(sample_keys) == len(values)):
            keys = [str(key) for key in sample_keys]
        else:
            keys = [f"pos:{index}" for index in range(len(values))]
    frames = window.get("frame_identifiers") if isinstance(window.get("frame_identifiers"), Sequence) else ()
    records: list[dict[str, Any]] = []
    for index, (key, value) in enumerate(zip(keys, values)):
        frame = frames[index] if index < len(frames) and isinstance(frames[index], Mapping) else {}
        device = frame.get("device_id")
        records.append({
            "key": key,
            "ordinal": index,
            "value": value,
            "query_rows": _finite(frame.get("query_rows")),
            "sequences": _finite(frame.get("sequences_per_replica")),
            "tokens": _finite(frame.get("tokens_per_sequence")),
            "device": "" if device in (None, "") else str(device),
            "forward_id": str(frame.get("forward_id") or ""),
        })
    return records


def _geometry_groups(window: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Usable geometry buckets in retained input order. Counts only, no spans."""
    raw = window.get("geometry_populations")
    if not isinstance(raw, Mapping):
        return []
    groups: list[dict[str, Any]] = []
    for key, count in raw.items():
        parts: dict[str, float | None] = {}
        for piece in str(key).split(","):
            if "=" not in piece:
                continue
            name, value = piece.split("=", 1)
            token = value.strip()
            parts[name.strip()] = None if token.lower() in {"", "none", "null"} else _finite(token)
        query, sequences, tokens = parts.get("q"), parts.get("seq"), parts.get("tok")
        if query is None and sequences is None and tokens is None:
            continue
        number = _finite(count)
        if number is None or number <= 0:
            continue
        groups.append({"q": query, "seq": sequences, "tok": tokens, "count": int(number)})
    return groups


def _bind_primary(records: Sequence[Mapping[str, Any]], groups: Sequence[Mapping[str, Any]]) -> tuple[list[Mapping[str, Any]], dict[str, Any]] | None:
    """Largest complete forward count. Equal counts keep the earliest group."""
    best = max(int(group["count"]) for group in groups)
    primary = next(group for group in groups if int(group["count"]) == best)
    queries = [group["q"] for group in groups]
    if primary["q"] is not None and queries.count(primary["q"]) == 1:
        selected = [row for row in records if _same_number(row["query_rows"], primary["q"])]
    else:
        selected = []
        for row in records:
            if primary["q"] is not None and not _same_number(row["query_rows"], primary["q"]):
                continue
            if primary["seq"] is not None and (row["sequences"] is None or not _same_number(row["sequences"], primary["seq"])):
                return None
            if primary["tok"] is not None and (row["tokens"] is None or not _same_number(row["tokens"], primary["tok"])):
                return None
            selected.append(row)
    if len(selected) != int(primary["count"]):
        return None
    return list(selected), {
        "query_rows": primary["q"],
        "sequences_per_replica": primary["seq"],
        "tokens_per_sequence": primary["tok"],
    }


def _capture_root(observation: Mapping[str, Any] | None) -> Path | None:
    """The leaf that supplied both the duration windows and the client proof.

    ``source.directory`` is only a relocation hint. It may not override an
    explicit per-window receipt or ``source.path``; a hint is accepted only
    when its ``kernel_details.csv`` is the same file as the explicit leaf.
    """
    if not isinstance(observation, Mapping):
        return None
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    window = _window(observation)
    pointed: list[str] = []
    for name in ("source_path", "raw_path"):
        value = window.get(name)
        if isinstance(value, str) and value:
            pointed.append(value)
    for name in ("receipt_source_identity", "source_fingerprint"):
        identity = window.get(name)
        if isinstance(identity, Mapping) and isinstance(identity.get("path"), str):
            pointed.append(str(identity["path"]))
    for name in ("path", "sha256_source_path", "reported_source_path"):
        value = source.get(name)
        if isinstance(value, str) and value:
            pointed.append(value)
    expected: Path | None = None
    for value in pointed:
        path = Path(value)
        if path.name == "kernel_details.csv":
            expected = path
            break
        candidate = path / "kernel_details.csv"
        if candidate.is_file():
            expected = candidate
            break
    if expected is not None:
        return expected.parent
    directory = source.get("directory")
    if isinstance(directory, str) and directory and expected is None:
        return Path(directory)
    return None


def _b1_certified(observation: Mapping[str, Any] | None, records: Sequence[Mapping[str, Any]]) -> bool:
    """One ok request, concurrency 1, max_running 1, and one device on the capture root.

    Missing frame sequences do not withhold this binding. A forecast
    ``sequences_per_replica`` is not read. ``max_running`` other than 1 stays open.
    """
    devices = {str(row.get("device") or "") for row in records}
    devices.discard("")
    if len(devices) != 1:
        return False
    root = _capture_root(observation)
    if root is None or not root.is_dir():
        return False
    import fleet_archive_producer as producer
    files = producer._producer_files(root / "kernel_details.csv")
    if not any(role in files for role in ("benchmark_summary", "client_cell", "run_meta", "cellset")):
        return False
    documents = producer._load_producer_documents(files, {}, [], [])
    requests = producer._request_rows(documents.get("usage"))
    if not requests:
        return False
    concurrency = producer._concurrency({}, documents, requests)
    running = producer._batch(concurrency, documents).get("max_running")
    proof = producer._one_request_sequence_proof(requests, concurrency, running)
    return proof in {"one_ok_request_concurrency_one_max_running_one", "one_ok_request_concurrency_one"}


def _prefill_body_receipt(observation: Mapping[str, Any] | None) -> bool:
    return str(_window(observation).get("boundary") or "").endswith("_prefill_chunk")




@functools.lru_cache(maxsize=1)
def _dsh_source_declarations() -> dict[str, dict[str, Any]]:
    """Original DSH source registry keyed by the exact recorded source path."""
    path = Path(__file__).resolve().parent / "results" / "dsh_full_generalization.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    declared: dict[str, dict[str, Any]] = {}
    for item in document.get("heldout_cases") or ():
        if not isinstance(item, Mapping):
            continue
        source = item.get("path")
        if isinstance(source, str) and source:
            declared[str(Path(source))] = dict(item)
    return declared


def _cross_tp_selector(window: Mapping[str, Any]) -> bool | None:
    """The DSH producer's declared population selector, not a timing choice."""
    source = window.get("source_path") or window.get("raw_path")
    if not isinstance(source, str) or not source:
        return None
    record = _dsh_source_declarations().get(str(Path(source)))
    if record is None or "cross_tp_transfer" not in record:
        return None
    return record.get("cross_tp_transfer") is True

def _source_population(records: Sequence[Mapping[str, Any]],
                       window: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    """Use source-declared logical populations when the receipt covers every window.

    This is a producer-schema rule, not a caller label. The physical
    ``geometry_populations`` bucket can merge a padded logical population
    (e.g. q=3 into physical q=4). The original receipt retains output_query_rows
    and one mean per logical population. Only a complete, non-overlapping
    partition with at least two populations is used; otherwise the existing
    largest-complete-forward rule remains in force.
    """
    pointed = window.get("window_source")
    if not isinstance(pointed, str) or not pointed:
        return None
    try:
        document = json.loads(Path(pointed).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    observed = document.get("observed") if isinstance(document, Mapping) else None
    if not isinstance(observed, Mapping):
        return None
    groups = observed.get("geometry_groups")
    if not isinstance(groups, list) or len(groups) < 2:
        return None
    by_forward: dict[str, dict[str, Any]] = {}
    partitions: list[dict[str, Any]] = []
    for item in groups:
        if not isinstance(item, Mapping):
            return None
        geometry = item.get("geometry") if isinstance(item.get("geometry"), Mapping) else {}
        ids = item.get("forward_ids")
        span = item.get("body_forward_span_ms")
        mean = span.get("mean") if isinstance(span, Mapping) else None
        number = _finite(mean)
        if (not isinstance(ids, list) or not ids or number is None
                or len(set(map(str, ids))) != len(ids)):
            return None
        forward_ids = {str(value) for value in ids}
        if any(forward_id in by_forward for forward_id in forward_ids):
            return None
        query = geometry.get("output_query_rows")
        if query is None:
            query = geometry.get("query_rows")
        partitions.append({"q": _finite(query), "count": len(forward_ids),
                           "mean": number, "forward_ids": sorted(forward_ids)})
        for forward_id in forward_ids:
            by_forward[forward_id] = {"q": _finite(query), "mean": number}
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    for record in records:
        forward_id = str(record.get("forward_id") or "")
        match = by_forward.get(forward_id)
        if match is None:
            return None
        if forward_id in covered:
            return None
        covered.add(forward_id)
        selected.append({**record, "value": match["mean"], "source_population_q": match["q"]})
    if covered != set(by_forward):
        return None
    if len(selected) != sum(part["count"] for part in partitions):
        return None
    cross_tp = _cross_tp_selector(window)
    if cross_tp is True:
        chosen = partitions[0]
        selected = [record for record in selected
                    if str(record.get("forward_id")) in chosen["forward_ids"]]
        if len(selected) != chosen["count"]:
            return None
        return selected, {"logical_populations": [chosen], "cross_tp_transfer": True}
    return selected, {"logical_populations": partitions,
                      "cross_tp_transfer": False if cross_tp is False else None}

def producer_contract(row: Mapping[str, Any], observation: Mapping[str, Any] | None,
                      values: Sequence[float], basis: str) -> dict[str, Any]:
    """Reducer and ordinal key set. This function does not read a target number or a phase string."""
    records = _frame_records(observation, values)
    explicit = _explicit_reducer(basis, row)
    if explicit is not None:
        return {"status": "ready", "reducer": explicit, "records": records,
                "producer": "explicit_" + explicit, "label": "explicit", "window_filter": {}}
    window = _window(observation)
    source_population = _source_population(records, window)
    if source_population is not None:
        selected, window_filter = source_population
        return {"status": "ready", "reducer": "mean", "records": selected,
                "producer": "source_declared_populations", "label": "source_population",
                "window_filter": window_filter}
    groups = _geometry_groups(window)
    if groups:
        bound = _bind_primary(records, groups)
        if bound is None:
            return {"status": "ambiguous", "reason": "population_unbound", "reducer": "",
                    "records": [], "producer": "largest_complete_forward_count",
                    "label": "", "window_filter": {}}
        selected, window_filter = bound
        return {"status": "ready", "reducer": "mean", "records": selected,
                "producer": "largest_complete_forward_count", "label": "primary",
                "window_filter": window_filter}
    if _prefill_body_receipt(observation) and len(records) > 1:
        certified = _b1_certified(observation, records)
        return {"status": "ready", "reducer": "sum", "records": records,
                "producer": _PREFILL_PRODUCER,
                "label": "certified" if certified else "conditional", "window_filter": {}}
    if len(records) == 1:
        return {"status": "ready", "reducer": "single", "records": records,
                "producer": "single_window", "label": "single", "window_filter": {}}
    return {"status": "ambiguous", "reason": "producer_unsupported", "reducer": "",
            "records": records, "producer": "unsupported", "label": "", "window_filter": {}}
