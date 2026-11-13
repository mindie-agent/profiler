"""Analysis orchestration for the compact MindIE profiler core.

[Role]
  Resolve explicit rank/window selection, probe and read one DB or CSV per
  rank, classify events, account each window, hand measured observations to
  the C7 report builder, then attach optional scene/steady/anomaly/modeling
  enrichment without changing the core accounting definitions.

[Invariants]
  * A request without an explicit window/full-range is rejected; step ids are
    never inferred.
  * DB schema errors are surfaced, not bypassed with a CSV fallback.
  * Every read is bounded by rows and wall time; schema/query timings are
    recorded.  Content SHA256 is opt-in (``hash_sources=False`` by default);
    the default identity is path+size_bytes+mtime_ns+schema_version.
  * Empty/incomplete windows produce limitations and ``None`` metrics, never
    fabricated zeros or conclusions.

[Timeouts & Locks]
  Per-window sqlite/CSV budgets default to 20s/30s and 1M/5M rows.  No lock is
  held while parsing or accounting.

[Side-Effect Policy]
  Reads source artifacts only.  The optional output JSON is written atomically
  by ``report.write_report``.
"""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .accounting import account_window
from .classify import apply as classify_events
from .enrichment import enrich_report
from .measured_supply import deployment_source_identity, image_digest
from .events import (
    Observation,
    ProfilerUsageError,
    QueryStats,
    SourceRef,
    Window,
)
from .report import build_report, write_report
from .segment import (
    RankSource,
    discover_rank_sources,
    resolve_ranks,
    validate_selection,
)
from .sources_csv import CsvSource, probe_csv
from .sources_db import DbSource, probe_db, sha256_file


def _add(limitations: list[dict], code: str, scope: str, detail: str, severity: str = "medium") -> None:
    for item in limitations:
        if item.get("code") == code and item.get("scope") == scope:
            return
    limitations.append({"code": code, "scope": scope, "detail": detail, "severity": severity})


def _normalize_windows(windows: Iterable[Window] | None) -> list[Window]:
    rows = list(windows or [])
    for index, window in enumerate(rows):
        if not isinstance(window, Window):
            raise ProfilerUsageError(f"window #{index} must be a Window, got {type(window).__name__}")
    return rows


def _mtime_ns(path: str) -> int | None:
    try:
        return int(Path(path).stat().st_mtime_ns)
    except TimeoutError:
        raise
    except OSError:
        return None


def _source_ref(
    item: RankSource,
    *,
    schema_version: str,
    schema_variant: str,
    sha256: str | None,
    size_bytes: int,
    header_sha256: str | None = None,
    optional_missing: Sequence[str] = (),
) -> SourceRef:
    path = item.db_path if item.kind == "db" else item.csv_path
    if not path:
        raise ProfilerUsageError(f"rank {item.rank_id!r} has no {item.kind} source path")
    return SourceRef(
        rank_id=item.rank_id,
        rank_index=item.rank_index,
        kind=str(item.kind),
        path=path,
        basename=Path(path).name,
        sha256=sha256,
        size_bytes=size_bytes,
        schema_version=schema_version,
        schema_variant=schema_variant,
        header_sha256=header_sha256,
        optional_missing=tuple(optional_missing),
        notes=item.notes,
        mtime_ns=_mtime_ns(path),
    )


def _observations_for_rank(
    item: RankSource,
    windows: list[Window],
    *,
    full_range: bool,
    hash_sources: bool,
    max_rows: int,
    query_timeout_s: float,
    csv_timeout_s: float,
    request_wall_ns: int | None,
    limitations: list[dict],
    query_timings: list[dict],
    schema_rows: list[dict],
) -> tuple[SourceRef, list[Observation]]:
    rank_id = item.rank_id
    source_path = item.db_path if item.kind == "db" else item.csv_path
    if not source_path:
        raise ProfilerUsageError(f"rank {rank_id!r} has no {item.kind} source")
    started = time.perf_counter()
    digest = sha256_file(source_path) if hash_sources else None
    hash_ms = round((time.perf_counter() - started) * 1000.0, 6)
    query_timings.append(
        {"rank_id": rank_id, "phase": "sha256", "elapsed_ms": hash_ms, "enabled": bool(hash_sources)}
    )
    if not hash_sources:
        _add(
            limitations,
            "sha256_disabled",
            rank_id,
            "content sha256 was not requested; identity uses path+size_bytes+mtime_ns+schema_version",
            "low",
        )

    if item.kind == "db":
        probe_started = time.perf_counter()
        schema = probe_db(source_path, timeout_s=query_timeout_s)
        probe_ms = round((time.perf_counter() - probe_started) * 1000.0, 6)
        query_timings.append(
            {"rank_id": rank_id, "phase": "schema_probe", "elapsed_ms": probe_ms, "schema_version": schema.schema_version}
        )
        source = _source_ref(
            item,
            schema_version=schema.exporter_schema_version,
            schema_variant=schema.schema_variant,
            sha256=digest,
            size_bytes=schema.size_bytes,
            optional_missing=schema.optional_missing,
        )
        db_source = DbSource(schema)
        if full_range:
            span = db_source.capture_range_ns(timeout_s=query_timeout_s)
            if span is None or span[1] <= span[0]:
                _add(limitations, "empty_source", rank_id, "DB contains no positive-length TASK/COMMUNICATION_OP rows", "high")
                query_windows = [Window(0, 1, label="full_range", source="full_range")]
            else:
                query_windows = [Window(span[0], span[1], label="full_range", source="full_range")]
        else:
            query_windows = list(windows)
        observations: list[Observation] = []
        for window in query_windows:
            events, stats = db_source.iter_window(
                window, max_rows=max_rows, timeout_s=query_timeout_s
            )
            for event in events:
                event.rank_id = rank_id
                event.rank_index = item.rank_index
            classify_events(events)
            accounting = account_window(events, window, request_wall_ns=request_wall_ns)
            stats.rank_id = rank_id
            stats.window_label = window.label or str(window.step)
            observations.append(
                Observation(
                    rank_id=rank_id,
                    rank_index=item.rank_index,
                    window=window,
                    accounting=accounting,
                    events=events,
                    source=source,
                    stats=stats,
                )
            )
            query_timings.append(
                {
                    "rank_id": rank_id,
                    "phase": "read",
                    "window": stats.window_label,
                    "rows_read": stats.rows_read,
                    "rows_selected": stats.rows_selected,
                    "elapsed_ms": stats.elapsed_ms,
                    "bad_rows": stats.bad_rows,
                    "unresolved_string_ids": stats.unresolved_string_ids,
                }
            )
        schema_rows.append(
            {
                "rank_id": rank_id,
                "kind": "db",
                "basename": source.basename,
                "schema_version": schema.schema_version,
                "schema_variant": schema.schema_variant,
                "tables": list(schema.tables),
                "optional_missing": list(schema.optional_missing),
                "block_column": schema.block_column,
                "mix_block_column": schema.mix_block_column,
                "shape_columns": list(schema.shape_columns),
                "has_wait_ns": schema.has_wait_ns,
                "size_bytes": schema.size_bytes,
            }
        )
        if schema.schema_version == "unversioned":
            _add(limitations, "schema_unversioned", rank_id, "META_DATA.SCHEMA_VERSION missing; verified columns were matched instead", "medium")
        if len(schema.shape_columns) < 3:
            _add(
                limitations,
                "shape_columns_absent",
                rank_id,
                "DB lacks some Input Shapes/Data Types/Formats columns; hotspot alignment reports an explicit unmodeled_reason.",
                "medium",
            )
        if schema.optional_missing:
            _add(
                limitations,
                "optional_table_absent",
                rank_id,
                "DB lacks optional tables: " + ", ".join(schema.optional_missing) + "; accounting uses the available COMPUTE_TASK_INFO/COMMUNICATION_OP rows",
                "low",
            )
        if any(obs.stats.unresolved_string_ids for obs in observations):
            _add(limitations, "unresolved_string_ids", rank_id, "STRING_IDS lacked ids used by selected rows; names are marked <unresolved:id>", "high")
        bad_db_rows = sum(obs.stats.bad_rows for obs in observations)
        if bad_db_rows:
            _add(limitations, "bad_db_rows", rank_id, f"{bad_db_rows} DB rows had null/non-positive timing and were skipped", "high")
        return source, observations

    probe_started = time.perf_counter()
    schema = probe_csv(source_path)
    probe_ms = round((time.perf_counter() - probe_started) * 1000.0, 6)
    query_timings.append(
        {"rank_id": rank_id, "phase": "schema_probe", "elapsed_ms": probe_ms, "schema_version": schema.schema_version}
    )
    source = _source_ref(
        item,
        schema_version=schema.schema_version,
        schema_variant=schema.schema_variant,
        sha256=digest,
        size_bytes=schema.size_bytes,
        header_sha256=schema.header_sha256,
        optional_missing=schema.optional_missing,
    )
    csv_source = CsvSource(schema, rank_id=rank_id, rank_index=item.rank_index)
    if full_range:
        broad = Window(0, 2**63 - 1, label="full_range", source="full_range")
        read = csv_source.read_windows([broad], max_rows=max_rows, timeout_s=csv_timeout_s)
        broad_events, broad_stats = read[0]
        if broad_events:
            first = min(event.start_ns for event in broad_events)
            last = max(event.end_ns for event in broad_events)
            query_windows = [Window(first, last, label="full_range", source="full_range")]
        else:
            query_windows = [Window(0, 1, label="full_range", source="full_range")]
        query_events = {0: broad_events}
        query_stats = {0: broad_stats}
    else:
        query_windows = list(windows)
        read = csv_source.read_windows(query_windows, max_rows=max_rows, timeout_s=csv_timeout_s)
        query_events = {index: values[0] for index, values in read.items()}
        query_stats = {index: values[1] for index, values in read.items()}
    observations = []
    for index, window in enumerate(query_windows):
        events = query_events.get(index, [])
        classify_events(events)
        accounting = account_window(events, window, request_wall_ns=request_wall_ns)
        stats = query_stats.get(index)
        if stats is None:
            stats = QueryStats(rank_id=rank_id, window_label=window.label or str(window.step), budget=max_rows)
        stats.rank_id = rank_id
        stats.window_label = window.label or str(window.step)
        observations.append(
            Observation(
                rank_id=rank_id,
                rank_index=item.rank_index,
                window=window,
                accounting=accounting,
                events=events,
                source=source,
                stats=stats,
            )
        )
        query_timings.append(
            {
                "rank_id": rank_id,
                "phase": "read",
                "window": stats.window_label,
                "rows_read": stats.rows_read,
                "rows_selected": stats.rows_selected,
                "elapsed_ms": stats.elapsed_ms,
                "bad_rows": stats.bad_rows,
                "shared_scan": True,
            }
        )
    schema_rows.append(
        {
            "rank_id": rank_id,
            "kind": "csv",
            "basename": source.basename,
            "schema_version": schema.schema_version,
            "schema_variant": schema.schema_variant,
            "header_sha256": schema.header_sha256,
            "columns": len(schema.header),
            "block_column": schema.block_column,
            "mix_block_column": schema.mix_block_column,
            "optional_missing": list(schema.optional_missing),
            "size_bytes": schema.size_bytes,
        }
    )
    if schema.optional_missing:
        _add(
            limitations,
            "optional_csv_column_absent",
            rank_id,
            "CSV lacks optional columns: " + ", ".join(schema.optional_missing),
            "low",
        )
    bad_rows = max((obs.stats.bad_rows for obs in observations), default=0)
    if bad_rows:
        _add(limitations, "bad_csv_rows", rank_id, f"{bad_rows} CSV rows lacked valid start/duration and were skipped", "high")
    return source, observations


_DEPLOYMENT_STATUS_ANCESTORS = 6
_MAX_STATUS_JSON_BYTES = 4 * 1024 * 1024
_CAPTURE_SUBDIR_RE = re.compile(
    r"^(?:"
    r"ascend_profiler_output|mindstudio_profiler_output|profile|"
    r"prof_[a-z0-9_.-]+|device_\d+|node[_-]?\d+|\d{1,3}(?:\.\d{1,3}){3}|"
    r"(?:pf|dc|prefill|decode|bench|warmup)(?:[_-][a-z0-9_.-]+)?"
    r")$",
    re.IGNORECASE,
)


def _is_internal_capture_dir(directory: Path) -> bool:
    name = directory.name
    folded = name.lower()
    if "rank" in folded or "_ascend_" in folded or _CAPTURE_SUBDIR_RE.match(name):
        return True
    return directory.parent.name.lower() == "profile"


def _capture_deployment_image(root: str | Path) -> tuple[str | None, str]:
    """Read the nearest same-capture status.json prepare record, bounded."""
    current = Path(root).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for _ in range(_DEPLOYMENT_STATUS_ANCESTORS + 1):
        path = current / "status.json"
        if path.is_file():
            try:
                if path.stat().st_size > _MAX_STATUS_JSON_BYTES:
                    return None, "invalid_capture_status"
                data = json.loads(path.read_text(encoding="utf-8"))
            except TimeoutError:
                raise
            except (OSError, ValueError, UnicodeError):
                return None, "invalid_capture_status"
            if not isinstance(data, Mapping):
                return None, "invalid_capture_status"
            digests = set()
            prepare = data.get("prepare")
            if isinstance(prepare, Sequence) and not isinstance(prepare, (str, bytes)):
                for item in prepare:
                    if not isinstance(item, Mapping):
                        continue
                    if item.get("created") is False or item.get("success") is False:
                        continue
                    digest = image_digest(
                        item.get("image_id")
                        or item.get("oci_image_digest")
                        or item.get("deployment_image_id")
                    )
                    if digest:
                        digests.add(digest)
            if len(digests) == 1:
                return next(iter(digests)), "capture_status_prepare"
            if len(digests) > 1:
                return None, "ambiguous_capture_prepare"
            return None, "capture_status_without_prepare"
        parent = current.parent
        if (
            parent == current
            or not _is_internal_capture_dir(current)
            or parent.name.startswith("pytest-")
            or parent.name in {"tmp", "temp", "var", "private", "Users", "home"}
        ):
            break
        current = parent
    return None, "absent"


def analyze_profile(
    root: str | Path,
    *,
    ranks: Iterable[str] | None = None,
    windows: Iterable[Window] | None = None,
    full_range: bool = False,
    source: str = "auto",
    top_n: int = 8,
    hash_sources: bool = False,
    max_rows: int = 1_000_000,
    query_timeout_s: float = 20.0,
    csv_timeout_s: float = 30.0,
    group_by: str = "variant",
    request_wall_ms: float | None = None,
    aic_count: int | None = None,
    deployment_image_id: str | None = None,
    sparse_geometry: Mapping[str, Any] | None = None,
    scene: dict[str, Any] | None = None,
    model_provider: Any | None = None,
    model_inputs: Any | None = None,
    model_hardware: Any | None = None,
    steady_config: Any | None = None,
    structure: Any | None = None,
    structure_bindings: Any | None = None,
    structure_correlations: Sequence[Any] | None = None,
    structure_module_traces: Sequence[str | Path] | None = None,
    mapping_limit: int = 200,
    max_mapping_events: int = 100_000,
    output: str | Path | None = None,
) -> dict:
    """Analyze explicit windows and return the enriched C7 report dict.

    ``windows`` must carry explicit nanosecond bounds.  Use
    ``segment.parse_step_windows`` / ``parse_windows`` for CLI-style parsing.

    Optional modeling injection is explicit: ``model_provider`` must implement
    the versioned provider protocol, ``model_inputs`` must be keyed by kernel
    name/rank, and ``model_hardware`` is only used when the supplied kernel
    inputs omit hardware.  Without both provider and inputs, hotspot fields
    remain ``unmodeled`` with a reason.  Core accounting definitions are never
    replaced by the enrichment fragment.
    """

    started = time.perf_counter()
    if structure is None and (
        structure_bindings is not None or structure_correlations or structure_module_traces
    ):
        raise ProfilerUsageError("structure bindings/correlations/module traces require a structure manifest")
    if top_n <= 0:
        raise ProfilerUsageError("top_n must be positive")
    if max_rows <= 0:
        raise ProfilerUsageError("max_rows must be positive")
    if group_by not in {"variant", "kernel"}:
        raise ProfilerUsageError("group_by must be 'variant' or 'kernel'")
    request_wall_ns: int | None = None
    if request_wall_ms is not None:
        if (
            not isinstance(request_wall_ms, (int, float))
            or not math.isfinite(float(request_wall_ms))
            or request_wall_ms < 0
        ):
            raise ProfilerUsageError("request_wall_ms must be a finite non-negative number")
        request_wall_ns = int(round(float(request_wall_ms) * 1_000_000))
    if aic_count is not None and (
        isinstance(aic_count, bool) or not isinstance(aic_count, int) or aic_count <= 0
    ):
        raise ProfilerUsageError("aic_count must be a positive integer")
    if sparse_geometry is not None and not isinstance(sparse_geometry, Mapping):
        raise ProfilerUsageError("sparse_geometry must be a mapping")
    selected_windows = _normalize_windows(windows)
    validate_selection(selected_windows, full_range=full_range)
    requested_steps = sorted({window.step for window in selected_windows if window.step is not None})

    normalized_root = Path(root).expanduser().resolve()
    discovered = discover_rank_sources(normalized_root, source=source)
    sources = resolve_ranks(discovered, ranks)
    if not sources:
        raise ProfilerUsageError("no ranks selected")
    limitations: list[dict] = []
    query_timings: list[dict] = []
    schema_rows: list[dict] = []
    observations: list[Observation] = []
    source_refs: list[SourceRef] = []

    if ranks is None:
        _add(
            limitations,
            "rank_not_selected",
            "global",
            "No --rank filter was supplied; all discovered ranks are included and no target rank was inferred.",
            "medium",
        )
    if len(sources) == 1:
        _add(limitations, "single_rank", sources[0].rank_id, "Only one rank was selected; cross-rank slowest analysis is unavailable.", "medium")
    if not requested_steps:
        _add(
            limitations,
            "step_not_provided",
            "global",
            "No explicit step was supplied; steady_steps is empty. Kernel detail rows have no step-id column, so no step was inferred.",
            "high",
        )
    if (not scene or not scene.get("clock_domain")) and len(sources) > 1:
        _add(limitations, "clock_domain_unknown", "global", "Cross-rank comparison assumes comparable clocks; no --clock-domain was supplied.", "medium")

    for item in sources:
        source_ref, rank_observations = _observations_for_rank(
            item,
            selected_windows,
            full_range=full_range,
            hash_sources=hash_sources,
            max_rows=max_rows,
            query_timeout_s=max(0.1, query_timeout_s),
            csv_timeout_s=max(0.1, csv_timeout_s),
            request_wall_ns=request_wall_ns,
            limitations=limitations,
            query_timings=query_timings,
            schema_rows=schema_rows,
        )
        source_refs.append(source_ref)
        observations.extend(rank_observations)
        for observation in rank_observations:
            accounting = observation.accounting
            if not accounting.available:
                _add(
                    limitations,
                    "empty_window",
                    f"{item.rank_id}:{observation.window.label or observation.window.step}",
                    "Selected window contains no kernel events; accounting metrics are null (not zero).",
                    "high",
                )
            elif accounting.coverage_ratio is not None and accounting.coverage_ratio < 0.98:
                _add(
                    limitations,
                    "partial_window_coverage",
                    f"{item.rank_id}:{observation.window.label or observation.window.step}",
                    f"Observed event span covers {accounting.coverage_ratio:.1%} of the requested window; "
                    "head/tail idle outside the span is not included in observed_event_span/device_uncovered.",
                    "medium",
                )

    expected_rank_ids = {source.rank_id for source in source_refs}
    if requested_steps:
        observed = {
            (obs.rank_id, obs.window.step)
            for obs in observations
            if obs.window.step is not None and obs.accounting.available
        }
        for rank_id in sorted(expected_rank_ids):
            for step in requested_steps:
                if (rank_id, step) not in observed:
                    _add(
                        limitations,
                        "rank_step_missing",
                        f"{rank_id}:step_{step}",
                        "No kernel events for this explicit rank/step window; medians exclude it.",
                        "high",
                    )
    if model_provider is None and model_inputs is None:
        _add(
            limitations,
            "modeling_not_run",
            "global",
            "No model provider or kernel inputs were supplied; ideal lower bounds and model predictions remain null with an unmodeled_reason.",
            "high",
        )

    status_digest, status_basis = _capture_deployment_image(normalized_root)
    if status_basis == "invalid_capture_status":
        _add(
            limitations,
            "invalid_capture_status",
            "global",
            "Same-capture status.json could not be parsed; deployment image identity was not certified from status.json.",
            "medium",
        )
    elif status_basis == "ambiguous_capture_prepare":
        _add(
            limitations,
            "ambiguous_capture_prepare",
            "global",
            "Same-capture status.json recorded multiple distinct prepare image digests; deployment image identity was not certified from status.json.",
            "medium",
        )
    declared_digest = image_digest(deployment_image_id) if deployment_image_id else ""
    if status_digest and declared_digest:
        if status_digest == declared_digest:
            source_identity = deployment_source_identity(
                declared_digest, basis="capture_status_and_user_declared"
            )
        else:
            _add(
                limitations,
                "conflicting_deployment_image_identity",
                "global",
                "Explicit --deployment-image-id disagrees with same-capture status.json prepare digest; deployment source was marked conflicting and not certified.",
                "high",
            )
            source_identity = {
                "source_scope": "conflicting",
                "image_digest": None,
                "basis": "conflicting_status_and_user_declared",
                "status_image_digest": status_digest,
                "declared_image_digest": declared_digest,
            }
    elif declared_digest:
        source_identity = deployment_source_identity(declared_digest, basis="user_declared")
    elif status_digest:
        source_identity = deployment_source_identity(status_digest, basis=status_basis)
    else:
        source_identity = deployment_source_identity(None, basis=status_basis)

    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 6)
    report = build_report(
        sources=source_refs,
        observations=observations,
        requested_steps=requested_steps,
        scene=scene or {},
        scene_provided=bool(scene),
        limitations=limitations,
        query_timings=query_timings,
        elapsed_ms=elapsed_ms,
        schema_rows=schema_rows,
        output_path=str(output) if output is not None else None,
        top_n=top_n,
        group_by=group_by,
    )
    report = enrich_report(
        report,
        observations=observations,
        requested_steps=requested_steps,
        scene=scene or {},
        model_provider=model_provider,
        model_inputs=model_inputs,
        model_hardware=model_hardware,
        steady_config=steady_config,
        physical_owners=aic_count,
        source_identity=source_identity,
        sparse_geometry=sparse_geometry,
    )
    report["enrichment"]["deployment_source"] = dict(source_identity)
    if structure is not None:
        from .structure_mapping import map_structure

        report["structure_mapping"] = map_structure(
            observations, structure, bindings=structure_bindings,
            correlations=structure_correlations, mapping_limit=mapping_limit,
            module_traces=structure_module_traces,
            max_events=max_mapping_events,
            phase=(scene or {}).get("phase"),
        )
    from .collective_readiness import read_collective_readiness

    readiness_windows = (
        None
        if full_range or not selected_windows
        else [(w.start_ns, w.end_ns) for w in selected_windows]
    )
    report["collective_readiness"] = read_collective_readiness(
        normalized_root,
        source=source,
        ranks=[item.rank_id for item in sources],
        windows=readiness_windows,
        timeout_s=max(0.1, query_timeout_s),
    )
    if output is not None:
        write_report(report, output)
    return report
