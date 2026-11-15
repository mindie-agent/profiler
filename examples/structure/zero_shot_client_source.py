"""Original retained client-request source for the fixed 731 zero-shot cells.

[Role]
  Read each original cell's retained client JSON (the producer's literal
  ``streams``/``first_token_latencies_s``/prompt/result record), expose every
  per-stream request with its natural units and client boundary, resolve the
  launch ordinal only by an exact value match to the launch-order
  ``first_token_latencies_s`` list, and keep cell aggregates separate from
  request measurements.  Rank/worker/service association is linked from the
  approved native source index without changing that reader.

[Invariants]
  * Values are preserved in their producer units: TTFT/e2e/ITL/TPOT are
    seconds; token/chunk counts are integers; ``started`` is UTC wallclock.
  * TTFT is client send -> first SSE chunk; e2e is send -> last SSE chunk; ITL
    is consecutive chunk arrival.  These are never device-forward spans.
  * ``streams`` is producer-sorted by TTFT, not launch order.  A launch ordinal
    is assigned only when exactly one ``first_token_latencies_s`` entry matches
    the stream's TTFT value; duplicates remain ambiguous.  No request ID is
    invented.
  * Cell aggregates (ttft_mean/p50, tpot_mean/p50, window_s,
    measure_window_s, out_tokens_per_s) are retained as aggregates only and
    never substituted for a request L4 value.
  * Missing/empty/partial/conflict/out-of-domain states remain explicit and the
    original cell stays in the denominator.

[Timeouts & Locks]
  Bounded JSON reads and a cached measured-file index; no network, subprocess,
  device work or model execution.

[Side-Effect Policy]
  Read-only over source roots.  Returns frozen records; callers own output.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable, Iterator, Mapping, Sequence

SCHEMA_VERSION = "mindie-zero-shot-client-requests/1"
DEFAULT_SOURCE_ROOTS = (
    Path("/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107"),
    Path("/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack08-20261107"),
)
DEFAULT_PRODUCER_SEED = 1024
_UNITS = {
    "ttft_s": "seconds",
    "e2e_s": "seconds",
    "itl_mean_s": "seconds",
    "itl_p50_s": "seconds",
    "tpot_derived_s": "seconds",
    "ttft_mean_s": "seconds (cell aggregate)",
    "ttft_p50_s": "seconds (cell aggregate)",
    "tpot_mean_s": "seconds (cell aggregate)",
    "tpot_p50_s": "seconds (cell aggregate)",
    "window_s": "seconds (aggregate span, not cell duration)",
    "measure_window_s": "seconds (includes profile overhead)",
    "start_profile_s": "seconds",
    "completion_tokens": "tokens",
    "chunks": "stream chunks",
    "concurrency": "declared requests",
    "prompt_tokens": "tokens",
    "shared_tokens": "tokens",
    "fresh_tokens": "tokens",
    "max_tokens": "tokens",
}
_BOUNDARIES = {
    "ttft_s": "per-request client send -> first SSE chunk",
    "e2e_s": "per-request client send -> last SSE chunk",
    "itl_mean_s": "per-request consecutive SSE chunk arrival",
    "itl_p50_s": "per-request consecutive SSE chunk arrival",
    "tpot_derived_s": "producer formula (e2e-ttft)/max(1,completion-1), request-derived aggregate",
    "window_s": "max(e2e)-min(ttft) across successful streams; not cell duration",
    "measure_window_s": "client burst wallclock including profile/wait operations",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if out == out and out >= 0.0 else None


def _int(value: Any) -> int | None:
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out if out >= 0 else None


def iter_original_rows(path: Path | str) -> Iterator[dict[str, Any]]:
    """Stream the fixed original JSONL without copying the population."""
    source = Path(path)
    opener = gzip.open if source.name.endswith(".gz") else open
    with opener(source, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def iter_original_rows_with_sha(path: Path | str) -> Iterator[tuple[dict[str, Any], str]]:
    """Stream rows with the exact original JSONL line SHA-256 (newline excluded)."""
    source = Path(path)
    opener = gzip.open if source.name.endswith(".gz") else open
    with opener(source, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line), hashlib.sha256(line.encode()).hexdigest()


@lru_cache(maxsize=8)
def _measured_index(root_names: tuple[str, ...]) -> dict[str, tuple[Path, ...]]:
    """Exact cell_id -> measured JSON paths; duplicates stay visible."""
    found: dict[str, list[Path]] = defaultdict(list)
    for name in root_names:
        root = Path(name)
        out = root / "out"
        if not out.is_dir():
            continue
        for path in sorted(out.glob("*/measured/*.json")):
            found[path.stem].append(path.resolve())
    return {key: tuple(value) for key, value in found.items()}


P6_SCHEMA = "mindie-profiler-client-request-interface/1"
P7_SCHEMA = "mindie-profiler-client-request-declaration/1"


def _join_streams(launch: Sequence[Any], streams: Sequence[Mapping[str, Any]]
                  ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Join launch ordinals to streams by exact producer rounding, never tolerance."""
    rounded: dict[float, list[int]] = defaultdict(list)
    for index, stream in enumerate(streams):
        ttft = _float(stream.get("ttft_s"))
        if ttft is not None:
            rounded[round(ttft, 6)].append(index)
    ordinals: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for ordinal, value in enumerate(launch):
        raw = float(value) if isinstance(value, (int, float)) and value > 0 else None
        if raw is None:
            ordinals.append({"launch_ordinal": ordinal, "raw_ttft_s": None,
                             "ttft_s": None, "stream_rank": None,
                             "join_status": "launch_ttft_absent",
                             "candidate_stream_ranks": ()})
            conflicts.append("launch_ttft_absent_or_nonpositive")
            continue
        rounded_value = round(raw, 6)
        candidates = tuple(rounded.get(rounded_value, ()))
        if len(candidates) == 1:
            ordinals.append({"launch_ordinal": ordinal, "raw_ttft_s": raw,
                             "ttft_s": rounded_value, "stream_rank": candidates[0],
                             "join_status": "exact_unique_rounded_ttft",
                             "candidate_stream_ranks": candidates})
        elif len(candidates) > 1:
            ordinals.append({"launch_ordinal": ordinal, "raw_ttft_s": raw,
                             "ttft_s": rounded_value, "stream_rank": None,
                             "join_status": "ambiguous_duplicate_rounded_ttft",
                             "candidate_stream_ranks": candidates})
        else:
            ordinals.append({"launch_ordinal": ordinal, "raw_ttft_s": raw,
                             "ttft_s": rounded_value, "stream_rank": None,
                             "join_status": "no_rounded_stream_match",
                             "candidate_stream_ranks": ()})
            conflicts.append("launch_ttft_without_rounded_stream")
    stream_rows: list[dict[str, Any]] = []
    for index, stream in enumerate(streams):
        ttft = _float(stream.get("ttft_s"))
        candidates = [row["launch_ordinal"] for row in ordinals
                      if index in row["candidate_stream_ranks"]]
        if len(candidates) == 1:
            joined_status = "exact_unique_ordinal"
            joined_ordinal = candidates[0]
        elif len(candidates) > 1:
            joined_status = "ambiguous_rounded_ttft"
            joined_ordinal = None
        else:
            joined_status = "no_launch_match"
            joined_ordinal = None
        stream_rows.append({"stream_rank": index, "ttft_s": ttft,
                            "joined_ordinal": joined_ordinal,
                            "join_status": joined_status,
                            "candidate_ordinals": tuple(candidates)})
    return ordinals, stream_rows, conflicts


@dataclass(frozen=True)
class ClientStream:
    cell_id: str
    stream_rank: int
    ttft_s: float | None
    e2e_s: float | None
    e2e_truncation_possible: bool
    completion_tokens: int | None
    chunks: int | None
    itl_mean_s: float | None
    itl_p50_s: float | None
    ok: bool
    joined_ordinal: int | None
    join_status: str
    candidate_ordinals: tuple[int, ...]
    token_chunk_aligned: bool
    itl_valid: bool
    boundaries: Mapping[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION, "kind": "client_stream",
            "cell_id": self.cell_id, "stream_rank": self.stream_rank,
            "ttft_s": self.ttft_s, "e2e_s": self.e2e_s,
            "e2e_truncation_possible": self.e2e_truncation_possible,
            "completion_tokens": self.completion_tokens, "chunks": self.chunks,
            "itl_mean_s": self.itl_mean_s, "itl_p50_s": self.itl_p50_s,
            "ok": self.ok, "joined_ordinal": self.joined_ordinal,
            "join_status": self.join_status,
            "candidate_ordinals": list(self.candidate_ordinals),
            "token_chunk_aligned": self.token_chunk_aligned,
            "itl_valid": self.itl_valid,
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True)
class ClientDeclaration:
    """Producer-declared launch ordinal, independent of any measured outcome."""
    key: str
    cell_id: str
    phase: str
    cohort: str
    producer: str
    rack: str
    ordinal: int
    concurrency: int
    prompt_tokens: int
    shared_tokens: int
    fresh_tokens: int
    mix_class: str
    mix_index: int | None
    mix_count: int
    prompt_seed: int
    request_seed: int
    seed_basis: str
    max_tokens: int
    chunk_budget: Any
    graph_mode: Any
    graph_capture_sizes: Any
    mixed_prompt: bool
    mode_boundary: str | None
    declaration_source: str
    declaration_status: str
    conditions: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": P7_SCHEMA, "cell_id": self.cell_id,
            "phase": self.phase, "cohort": self.cohort,
            "producer": self.producer, "rack": self.rack,
            "ordinal": self.ordinal, "concurrency": self.concurrency,
            "prompt_tokens": self.prompt_tokens,
            "shared_tokens": self.shared_tokens,
            "fresh_tokens": self.fresh_tokens,
            "mix_class": self.mix_class, "mix_index": self.mix_index,
            "mix_count": self.mix_count, "prompt_seed": self.prompt_seed,
            "request_seed": self.request_seed, "seed_basis": self.seed_basis,
            "max_tokens": self.max_tokens, "chunk_budget": self.chunk_budget,
            "graph_mode": self.graph_mode,
            "graph_capture_sizes": self.graph_capture_sizes,
            "mixed_prompt": self.mixed_prompt,
            "mode_boundary": self.mode_boundary,
            "declaration_source": self.declaration_source,
            "declaration_status": self.declaration_status,
            "conditions": dict(self.conditions),
        }


@dataclass(frozen=True)
class ClientRequest:
    """One launch-ordinal TTFT key; stream metadata only when the join is exact."""
    key: str
    client_id: str
    cell_id: str
    phase: str
    producer: str
    rack: str
    launch_ordinal: int
    raw_ttft_s: float | None
    ttft_s: float | None
    ttft_boundary: str
    stream_join_status: str
    stream_rank: int | None
    candidate_stream_ranks: tuple[int, ...]
    ok: bool | None
    e2e_s: float | None
    e2e_truncation_possible: bool | None
    itl_mean_s: float | None
    itl_p50_s: float | None
    tpot_derived_s: float | None
    completion_tokens: int | None
    chunks: int | None
    itl_valid: bool | None
    token_chunk_aligned: bool | None
    request_seed: int
    prompt_seed: int
    prompt_tokens: int | None
    shared_tokens: int | None
    fresh_tokens: int | None
    mix_class: str
    mix_index: int | None
    mix_count: int
    seed_basis: str
    capture_context: Mapping[str, Any]
    source_sha256: str
    measured_path: str
    original_row_sha256: str
    original_row_sha_basis: str

    @property
    def ttft_ms(self) -> float | None:
        return None if self.ttft_s is None else self.ttft_s * 1000.0

    @property
    def e2e_ms(self) -> float | None:
        return None if self.e2e_s is None else self.e2e_s * 1000.0

    @property
    def observed_stream(self) -> dict[str, Any] | None:
        if self.stream_rank is None:
            return None
        return {
            "ok": self.ok, "e2e_s": self.e2e_s,
            "e2e_truncation_possible": self.e2e_truncation_possible,
            "itl_mean_s": self.itl_mean_s, "itl_p50_s": self.itl_p50_s,
            "completion_tokens": self.completion_tokens, "chunks": self.chunks,
            "itl_valid": self.itl_valid,
            "token_chunk_aligned": self.token_chunk_aligned,
            "tpot_derived_s": self.tpot_derived_s,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION, "kind": "client_request",
            "key": self.key, "client_id": self.client_id, "cell_id": self.cell_id,
            "phase": self.phase, "producer": self.producer, "rack": self.rack,
            "launch_ordinal": self.launch_ordinal,
            "raw_ttft_s": self.raw_ttft_s, "ttft_s": self.ttft_s,
            "ttft_ms": self.ttft_ms, "ttft_boundary": self.ttft_boundary,
            "stream_join_status": self.stream_join_status,
            "stream_rank": self.stream_rank,
            "candidate_stream_ranks": list(self.candidate_stream_ranks),
            "observed_stream": (None if self.stream_rank is None else {
                "ok": self.ok, "e2e_s": self.e2e_s,
                "e2e_truncation_possible": self.e2e_truncation_possible,
                "itl_mean_s": self.itl_mean_s, "itl_p50_s": self.itl_p50_s,
                "completion_tokens": self.completion_tokens, "chunks": self.chunks,
                "itl_valid": self.itl_valid,
                "token_chunk_aligned": self.token_chunk_aligned,
                "tpot_derived_s": self.tpot_derived_s,
            }),
            "request_seed": self.request_seed, "prompt_seed": self.prompt_seed,
            "prompt_tokens": self.prompt_tokens,
            "shared_tokens": self.shared_tokens,
            "fresh_tokens": self.fresh_tokens,
            "mix_class": self.mix_class, "mix_index": self.mix_index,
            "mix_count": self.mix_count,
            "seed_basis": self.seed_basis,
            "capture_context": dict(self.capture_context),
            "source_sha256": self.source_sha256,
            "measured_path": self.measured_path,
            "original_row_sha256": self.original_row_sha256,
            "original_row_sha_basis": self.original_row_sha_basis,
            "units": dict(_UNITS), "boundaries": dict(_BOUNDARIES),
        }


@dataclass(frozen=True)
class ClientCapture:
    cell_id: str
    phase: str
    status: str
    reason: str | None
    measured_path: str
    measured_sha256: str | None
    size_bytes: int
    tag: str | None
    mode: str | None
    started: str | None
    bases: tuple[str, ...]
    concurrency: int | None
    prompt_tokens: int | None
    shared_tokens: int | None
    fresh_tokens: int | None
    max_tokens: int | None
    success: int | None
    failed: int | None
    warmup_requests: int | None
    warmup_ok: int | None
    warmup: tuple[Mapping[str, Any], ...]
    start_profile: tuple[Any, ...]
    stop_profile: tuple[Any, ...]
    start_profile_s: float | None
    measure_window_s: float | None
    first_token_latencies_s: tuple[Any, ...]
    requests: tuple[ClientRequest, ...]
    cell_aggregate: Mapping[str, Any]
    conflicts: tuple[str, ...]
    out_of_domain: tuple[str, ...]
    request_id_status: str
    rank_sources: tuple[Mapping[str, Any], ...]
    hardware_families: tuple[str, ...]
    service_association: str
    units: Mapping[str, str]
    boundaries: Mapping[str, str]
    limitations: tuple[str, ...] = ()
    original_row_sha256: str = ""
    original_row_sha_basis: str = "unavailable"
    launch_declaration: Mapping[str, Any] = field(default_factory=dict)
    status_cell: Mapping[str, Any] = field(default_factory=dict)
    producer: Mapping[str, Any] = field(default_factory=dict)
    streams: tuple[ClientStream, ...] = ()
    mixed_prompt: bool = False
    mix_count: int | None = None
    mix_prompt_tokens: int | None = None
    full_join_count: int = 0
    ambiguous_join_count: int = 0
    mode_boundary: str | None = None
    source_conflicts: tuple[Mapping[str, Any], ...] = ()
    declarations: tuple[ClientDeclaration, ...] = ()
    declared_count: int | None = None
    declaration_status: str = "declaration_unknown"
    declaration_source: str = "none"
    missing_ordinals: tuple[int, ...] = ()
    orphan_ttfts: tuple[float, ...] = ()
    orphan_stream_ranks: tuple[int, ...] = ()
    outcome_status: str = "unknown"

    @property
    def prediction_declaration(self) -> dict[str, Any]:
        from zero_shot_client_projection import prediction_declaration as _impl
        return _impl(self)

    def p6_interface(self) -> dict[str, Any]:
        from zero_shot_client_projection import p6_interface as _impl
        return _impl(self)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION, "kind": "client_capture",
            "cell_id": self.cell_id, "phase": self.phase, "status": self.status,
            "reason": self.reason, "measured_path": self.measured_path,
            "measured_sha256": self.measured_sha256, "size_bytes": self.size_bytes,
            "tag": self.tag, "mode": self.mode,
            "mode_boundary": self.mode_boundary, "started": self.started,
            "bases": list(self.bases), "concurrency": self.concurrency,
            "prompt_tokens": self.prompt_tokens, "shared_tokens": self.shared_tokens,
            "fresh_tokens": self.fresh_tokens, "max_tokens": self.max_tokens,
            "success": self.success, "failed": self.failed,
            "warmup_requests": self.warmup_requests, "warmup_ok": self.warmup_ok,
            "warmup": [dict(item) for item in self.warmup],
            "start_profile": list(self.start_profile),
            "stop_profile": list(self.stop_profile),
            "start_profile_s": self.start_profile_s,
            "measure_window_s": self.measure_window_s,
            "first_token_latencies_s": list(self.first_token_latencies_s),
            "cell_aggregate": dict(self.cell_aggregate),
            "conflicts": list(self.conflicts),
            "out_of_domain": list(self.out_of_domain),
            "request_id_status": self.request_id_status,
            "rank_sources": [dict(item) for item in self.rank_sources],
            "hardware_families": list(self.hardware_families),
            "service_association": self.service_association,
            "original_row_sha256": self.original_row_sha256,
            "original_row_sha_basis": self.original_row_sha_basis,
            "launch_declaration": dict(self.launch_declaration),
            "status_cell": dict(self.status_cell),
            "prediction_declaration": self.prediction_declaration,
            "p6_interface": self.p6_interface(),
            "producer": dict(self.producer),
            "streams": [item.as_dict() for item in self.streams],
            "mixed_prompt": self.mixed_prompt, "mix_count": self.mix_count,
            "mix_prompt_tokens": self.mix_prompt_tokens,
            "full_join_count": self.full_join_count,
            "ambiguous_join_count": self.ambiguous_join_count,
            "source_conflicts": [dict(item) for item in self.source_conflicts],
            "declarations": [item.as_dict() for item in self.declarations],
            "declared_count": self.declared_count,
            "declaration_status": self.declaration_status,
            "declaration_source": self.declaration_source,
            "missing_ordinals": list(self.missing_ordinals),
            "orphan_ttfts": list(self.orphan_ttfts),
            "orphan_stream_ranks": list(self.orphan_stream_ranks),
            "outcome_status": self.outcome_status,
            "units": dict(self.units), "boundaries": dict(self.boundaries),
            "limitations": list(self.limitations),
            "requests": [item.as_dict() for item in self.requests],
        }


def _rank_sources(cell_id: str, root_names: tuple[str, ...],
                  *, include_hashes: bool = False) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """Link the cell to its approved native rank/worker exports (read-only)."""
    try:
        import zero_shot_native_windows as native
    except ModuleNotFoundError:
        return (), ()
    index = native._index(root_names)
    sources: list[Mapping[str, Any]] = []
    families: set[str] = set()
    for source in index.get(cell_id, ()):
        for path in source.traces:
            host = path.parent.parent.name
            worker = path.parent.name
            opstat_sha, devices, _ = native._read_opstat(path.parent / "op_statistic.csv")
            device = int(devices[0]) if len(devices) == 1 else None
            launch = native._launch_for(source.case_dir, host)
            rank, rank_basis, rank_conflict = native._worker_rank(launch, device, worker)
            hardware = native._hardware_for(source.case_dir, host)
            family = hardware.get("hardware_family")
            if family:
                families.add(str(family))
            item = {
                "host": host, "worker": worker, "device_id": device,
                "rank": rank, "rank_basis": rank_basis,
                "rank_conflict": rank_conflict,
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "opstat_sha256": opstat_sha,
                "hardware_family": family,
                "hardware_subtype": hardware.get("hardware_subtype"),
                "hardware_basis": hardware.get("hardware_basis"),
                "source_sha256": _sha256(path) if include_hashes else None,
            }
            sources.append(item)
    return tuple(sources), tuple(sorted(families))


def _cmd_args(text: str) -> dict[str, Any]:
    line = next((item for item in text.splitlines()
                 if "bench_cell.py" in item and "--" in item), "")
    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = line.split()
    args: dict[str, Any] = {}
    for index, token in enumerate(tokens):
        if token.startswith("--") and index + 1 < len(tokens):
            args[token[2:]] = tokens[index + 1]
    return args


@lru_cache(maxsize=512)
def _serve_graph(path_name: str, _stat: tuple[int, int]) -> dict[str, Any]:
    """Parse the actual server argv compilation-config; no runtime bucket inference."""
    path = Path(path_name)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"graph_mode": None, "graph_capture_sizes": None,
                "graph_source": "serve_script_unreadable",
                "serve_sha256": None}
    line = next((item for item in text.splitlines()
                 if item.lstrip().startswith("exec ") and "--compilation-config" in item),
                next((item for item in text.splitlines()
                      if "--compilation-config" in item), ""))
    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = line.split()
    config: dict[str, Any] = {}
    if "--compilation-config" in tokens:
        index = tokens.index("--compilation-config")
        if index + 1 < len(tokens):
            try:
                config = json.loads(tokens[index + 1])
            except ValueError:
                config = {}
    return {
        "graph_mode": config.get("cudagraph_mode"),
        "graph_capture_sizes": config.get("cudagraph_capture_sizes"),
        "graph_source": "server_argv_compilation_config" if config else "graph_unverified",
        "serve_sha256": _sha256(path),
    }


def _secondary_declaration(cell_id: str, phase: str, measured_path: Path,
                           raw: Mapping[str, Any], roots: tuple[str, ...]) -> dict[str, Any]:
    """Producer launch/status sidecars for num_requests, phase, chunk geometry, seed."""
    case_dir = measured_path.parent.parent
    case_name = case_dir.name
    suffix = cell_id[len(case_name) + 1:] if cell_id.startswith(case_name + "_") else cell_id
    cell_dir = case_dir / suffix
    cmd_path = cell_dir / "cmd.sh"
    if not cmd_path.is_file():
        cmd_path = case_dir / "cmd" / f"{suffix}.sh"
    cmd_sha = _sha256(cmd_path) if cmd_path.is_file() else None
    cmd_args = _cmd_args(cmd_path.read_text(encoding="utf-8", errors="replace")) \
        if cmd_path.is_file() else {}
    case_path = case_dir.parent.parent / "cases" / f"{case_name}.json"
    case_sha = _sha256(case_path) if case_path.is_file() else None
    case_doc = {}
    if case_path.is_file():
        try:
            case_doc = json.loads(case_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            case_doc = {}
    graph = {"graph_mode": (case_doc.get("compilation_config") or {}).get("cudagraph_mode"),
             "graph_capture_sizes": (case_doc.get("compilation_config") or {}).get(
                 "cudagraph_capture_sizes"),
             "graph_source": "case_json_compilation_config" if case_doc.get("compilation_config")
                             else "case_json_graph_absent",
             "serve_sha256": None}
    if not graph.get("graph_capture_sizes"):
        node = str((case_doc.get("nodes") or [""])[0])
        serve = case_dir / "remote_cfg" / node / "cfg" / f"serve_{case_name}_{node}.sh"
        if not serve.is_file():
            candidates = sorted((case_dir / "remote_cfg").glob(f"*/cfg/serve_{case_name}_*.sh"))
            serve = candidates[0] if candidates else serve
        if serve.is_file():
            stat = serve.stat()
            graph = {**_serve_graph(str(serve.resolve()), (stat.st_size, stat.st_mtime_ns)),
                     "graph_path": str(serve)}
    status_path = case_dir / "status.json"
    status_sha = _sha256(status_path) if status_path.is_file() else None
    status_doc = {}
    if status_path.is_file():
        try:
            status_doc = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            status_doc = {}
    status_cell = next((item for item in status_doc.get("cells") or ()
                        if isinstance(item, dict) and
                        (item.get("tag") == cell_id or item.get("name") == suffix)), {})
    return {
        "cmd_path": str(cmd_path) if cmd_path.is_file() else None,
        "cmd_sha256": cmd_sha,
        "cmd_args": {key: cmd_args.get(key) for key in (
            "mode", "prompt-tokens", "shared-tokens", "max-tokens",
            "concurrency", "warmup", "warmup-max-tokens",
            "warmup-prompt-tokens", "profile-seconds", "settle-seconds",
            "post-profile-wait", "seed", "tag", "mix-count", "mix-prompt-tokens") if key in cmd_args},
        "case_path": str(case_path) if case_path.is_file() else None,
        "case_sha256": case_sha,
        "server_chunk_budget": case_doc.get("max_num_batched_tokens"),
        "server_max_num_seqs": case_doc.get("max_num_seqs"),
        "server_nodes": case_doc.get("nodes"),
        "server_dp": case_doc.get("dp"),
        "server_tp": case_doc.get("tp"),
        "graph_mode": graph.get("graph_mode"),
        "graph_capture_sizes": graph.get("graph_capture_sizes"),
        "graph_source": graph.get("graph_source"),
        "graph_path": graph.get("graph_path"),
        "serve_sha256": graph.get("serve_sha256"),
        "mix_prompt_tokens": raw.get("mix_prompt_tokens"),
        "source_token_geometry": "producer ids(prompt_seed,shared_tokens)+"
                                 "ids(prompt_seed+ordinal+1,fresh_tokens); token ids not exported",
        "cmd_seed": cmd_args.get("seed"),
        "seed_declared": cmd_args.get("seed"),
        "seed_effective": int(cmd_args["seed"]) if str(cmd_args.get("seed", "")).isdigit() else DEFAULT_PRODUCER_SEED,
        "seed_basis": ("cmd_declared" if cmd_args.get("seed") is not None
                       else "producer_default_1024"),
        "status_path": str(status_path) if status_path.is_file() else None,
        "status_sha256": status_sha,
        "status_cell_started": status_cell.get("started"),
        "status_cell_finished": status_cell.get("finished"),
        "status_cell_captured": status_cell.get("captured"),
        "status_cell_export": status_cell.get("export"),
    }


def _producer_info(measured_path: Path) -> dict[str, Any]:
    """Producer role and exact source digest from the real campaign root."""
    try:
        root = measured_path.parents[3]
    except IndexError:
        root = measured_path.parent
    rack = ("rack06" if "rack06" in root.name else
            "rack08" if "rack08" in root.name else "unknown")
    bench = root / "bin" / "bench_cell.py"
    variant = {"rack06": "rack06_any_choices_sse",
               "rack08": "rack08_nonempty_text_or_terminal_fallback"}.get(
                   rack, "unknown_producer")
    return {
        "rack": rack, "root": str(root), "producer_path": str(bench),
        "producer_sha256": _sha256(bench) if bench.is_file() else None,
        "producer_variant": variant,
        "ttft_boundary": ("client_send_to_first_sse_with_choices_may_empty"
                          if rack == "rack06" else
                          "client_send_to_first_nonempty_text_or_terminal_fallback"),
        "e2e_boundary": "client_send_to_read_loop_exit_or_response_close",
        "started_scope": "cell_utc",
        "per_request_start": "not_exported",
    }
