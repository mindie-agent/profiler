"""One explicit capture's scoped native caller followed by native observations.

[Role] Hold the per-capture prepared caller evidence once, apply the phase and
  geometry-scoped caller (capture_scoped_structure) before the maintained native
  observation profiles (native_observations), and give evaluators one compact
  final raw/identity to price.
[Invariants] Only declared geometry and retained windows select a caller; a
  missing scope stays honestly unbound while invalid evidence remains a
  distinct unsupported/conflict result. Observed values, forward counts and
  elapsed durations are never rewritten. Capture paths, hashes or sentinels
  never enter the physical predictor input. Prepared state belongs to one
  capture, is reused across its geometries and is released after jobs are
  materialised; there is no cross-capture prepared cache.
[Timeouts & Locks] One bounded CSV scan per prepared capture (delegated to the
  scoped evidence reader), one bounded observation read and one optional
  maintained extractor call. No locks, subprocesses or device work.
[Side-Effect Policy] Read-only capture access; returns copied inputs and
  provenance. Optional extraction writes only the caller-owned cache path.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from capture_scoped_evidence import MAX_SCAN_ROWS, SCAN_TIMEOUT_S
from capture_scoped_structure import prepare_scoped_capture


SCHEMA = "mindie-profiler-scoped-native-replay/1"
PREDICTION_SCHEMA = "mindie-profiler-final-prediction-input/1"
MAX_OBSERVATION_BYTES = 32 * 1024 * 1024
MAX_EXTRACTION_BYTES = 16 * 1024 * 1024
A5_HARDWARE_PREFIXES = ("Ascend950", "Ascend910_9599")
A5_HARDWARE_TOKENS = ("950", "9599")


class ReleasedScopedReplay(RuntimeError):
    """The one-capture prepared state was already released."""


def hardware_identity(raw):
    """Return the declared hardware key without inventing a platform."""
    machine = raw.get("machine") if isinstance(raw, dict) else None
    if not isinstance(machine, dict):
        return ""
    return str(machine.get("hardware_key") or machine.get("sku") or "")


def is_a5_machine(raw):
    """A5 covers 950DT/950PR and the 910_9599 alias used by Sim cases."""
    key = hardware_identity(raw)
    return (key.startswith(A5_HARDWARE_PREFIXES)
            or any(token in key for token in A5_HARDWARE_TOKENS))


def _observed_document(value):
    """Normalize a direct observation, extraction payload or bounded path."""
    if isinstance(value, (str, Path)):
        path = Path(value)
        if path.stat().st_size > MAX_OBSERVATION_BYTES:
            raise ValueError("scoped_observation_exceeds_bounded_read")
        document = json.loads(path.read_bytes())
    elif isinstance(value, dict):
        document = value
    elif value is None:
        return None
    else:
        raise ValueError("scoped_observation_requires_mapping_or_path")
    observed = document.get("observed") if isinstance(document.get("observed"), dict) else document
    return observed if isinstance(observed, dict) else None


def has_layer_spans(observation):
    """A slim body-only observation cannot select a native caller window."""
    observed = _observed_document(observation)
    if not observed or not isinstance(observed.get("forwards"), list):
        return False
    forwards = observed["forwards"]
    return bool(forwards) and all(
        isinstance(forward.get("layers"), list) and forward["layers"]
        and all(isinstance(layer, dict) and layer.get("start_ns") is not None
                and layer.get("end_ns") is not None for layer in forward["layers"])
        for forward in forwards)


def observation_forward_count(observation):
    observed = _observed_document(observation)
    forwards = (observed or {}).get("forwards")
    return len(forwards) if isinstance(forwards, list) else 0


def _query_rows(forward):
    rows = forward.get("query_rows") if isinstance(forward, dict) else None
    if type(rows) is not int or rows <= 0:
        raise ValueError("scoped_forward_geometry_malformed")
    return rows


def resolve_context_offset(observation, *, requested_context, hardware_a5,
                           explicit=None):
    """Infer an A5 truncated-prefill offset from requested context minus sumquery.

    Explicit observed contexts are never shifted: when any forward carries its
    own context, no offset is inferred. A caller-supplied offset remains an
    explicit declaration and is recorded as such.
    """
    if explicit is not None:
        if type(explicit) is not int or explicit < 0:
            raise ValueError("scoped_context_offset_malformed")
        return explicit, "caller_explicit"
    if not hardware_a5:
        return 0, "not_a5"
    observed = _observed_document(observation)
    forwards = (observed or {}).get("forwards")
    if not isinstance(forwards, list) or not forwards:
        return 0, "no_observed_forward"
    if any(forward.get("context", forward.get("context_tokens")) is not None
           for forward in forwards):
        return 0, "explicit_observed_context_present"
    if type(requested_context) is not int or requested_context <= 0:
        return 0, "requested_context_not_declared"
    total = sum(_query_rows(forward) for forward in forwards)
    if total <= 0 or total >= requested_context:
        return 0, "observation_covers_requested_context"
    return requested_context - total, "requested_context_minus_sumquery"


_FORWARD_FIELDS = (
    "forward_id", "phase", "query_rows", "tokens_per_sequence", "sequences",
    "context", "context_tokens",
)
_LAYER_FIELDS = (
    "layer_id", "start_ns", "end_ns", "first_csv_line", "last_csv_line",
)
_BODY_FIELDS = (
    "start_ns", "end_ns", "span_ms", "first_csv_line", "last_csv_line",
)


def _project_locators(value):
    evidence = value.get("evidence") if isinstance(value, dict) else None
    if not isinstance(evidence, dict):
        return None
    projected = {}
    for name in ("first_locator", "last_locator"):
        locator = evidence.get(name)
        if isinstance(locator, dict) and locator.get("csv_line") is not None:
            projected[name] = {"csv_line": locator["csv_line"]}
    return projected or None


def _project_extraction(document):
    """Keep only the fields the scoped reader needs; drop retained bulk text."""
    observed = _observed_document(document)
    if not isinstance(observed, dict):
        raise ValueError("full_extraction_requires_observation_mapping")
    project = {
        "schema_version": observed.get("schema_version"),
        "status": observed.get("status"),
        "body_span_sum_ms": observed.get("body_span_sum_ms"),
        "forwards": [],
    }
    forwards = observed.get("forwards")
    if not isinstance(forwards, list):
        raise ValueError("full_extraction_requires_forward_list")
    for forward in forwards:
        if not isinstance(forward, dict):
            raise ValueError("full_extraction_forward_not_mapping")
        item = {name: deepcopy(forward.get(name)) for name in _FORWARD_FIELDS
                if name in forward}
        body = forward.get("body")
        if isinstance(body, dict):
            item["body"] = {name: deepcopy(body.get(name))
                            for name in _BODY_FIELDS if name in body}
            locators = _project_locators(body)
            if locators:
                item["body"]["evidence"] = locators
        layers = forward.get("layers")
        if not isinstance(layers, list):
            raise ValueError("full_extraction_forward_requires_layers")
        item["layers"] = []
        for layer in layers:
            if not isinstance(layer, dict):
                raise ValueError("full_extraction_layer_not_mapping")
            projected = {name: deepcopy(layer.get(name))
                         for name in _LAYER_FIELDS if name in layer}
            locators = _project_locators(layer)
            if locators:
                projected["evidence"] = locators
            item["layers"].append(projected)
        project["forwards"].append(item)
    declared = observed.get("source_identity")
    if not isinstance(declared, dict) and isinstance(document, dict):
        declared = document.get("source_identity")
    if isinstance(declared, dict):
        project["source_identity"] = {
            name: deepcopy(declared.get(name))
            for name in ("path", "sha256", "size_bytes")}
    return project


def load_verified_extraction(path, *, capture_path=None, expected=None,
                             max_bytes=MAX_EXTRACTION_BYTES):
    """Load one current full observation with a bounded two-pass read.

    The expected cache/parser/config key is established by the caller from its
    trusted extraction record. A same-source payload produced by another parser
    or model configuration is stale, not verified. The source hash itself is
    checked by the scoped reader against the capture before binding.
    """
    source = Path(path)
    if not source.is_file():
        return None, {"status": "not_provided",
                      "reason": "full_extraction_not_present",
                      "path": str(source)}
    size = source.stat().st_size
    if size > max_bytes:
        raise ValueError("full_extraction_exceeds_bounded_read")
    content = sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            content.update(chunk)
    with source.open("rb") as handle:
        document = json.load(handle)
    after = source.stat()
    if after.st_size != size:
        raise ValueError("full_extraction_changed_during_read")
    record = {
        "cache_version": document.get("cache_version") if isinstance(document, dict) else None,
        "parser_identity": document.get("parser_identity") if isinstance(document, dict) else None,
        "cache_key": document.get("cache_key") if isinstance(document, dict) else None,
    }
    evidence = {"status": "current", "path": str(source),
                "sha256": content.hexdigest(), "size_bytes": size,
                "record": deepcopy(record)}
    if expected:
        for field in ("cache_version", "parser_identity", "cache_key",
                      "config_sha256"):
            wanted = expected.get(field)
            if wanted is not None and record.get(field) != wanted:
                return None, {"status": "stale",
                              "reason": "retained_extraction_identity_mismatch",
                              "field": field, "observed": record.get(field),
                              "expected": wanted,
                              "path": str(source)}
    observed = _project_extraction(document)
    del document
    if not has_layer_spans(observed):
        return None, {"status": "unavailable",
                      "reason": "extraction_has_no_complete_layer_spans",
                      "path": str(source), "sha256": evidence["sha256"]}
    declared = observed.get("source_identity")
    if isinstance(declared, dict):
        evidence["source_identity"] = deepcopy(declared)
    if capture_path is not None:
        capture = Path(capture_path)
        if not capture.is_file():
            return None, {"status": "not_provided",
                          "reason": "capture_csv_not_present",
                          "path": str(capture)}
        declared_size = (declared or {}).get("size_bytes")
        if type(declared_size) is int and declared_size != capture.stat().st_size:
            raise ValueError("extraction_source_size_mismatch")
        declared_path = (declared or {}).get("path")
        if declared_path:
            evidence["source_path_matches_capture"] = (
                Path(declared_path).resolve() == capture.resolve())
    return observed, evidence


def extract_full_observation(raw, capture_path, *, max_rows=MAX_SCAN_ROWS,
                             timeout_s=SCAN_TIMEOUT_S):
    """Use the maintained prefill extractor when no retained payload exists."""
    from mindie_sim.prediction.structure import parse_case
    from prefill import extract_file

    capture = Path(capture_path)
    if not capture.is_file():
        return None, {"status": "not_provided",
                      "reason": "capture_csv_not_present",
                      "path": str(capture)}
    case = parse_case(raw)
    config = case.model.to_dict()
    config["tp"] = case.runtime.parallel.tp
    observed = extract_file(capture, config, max_rows=max_rows,
                            timeout_s=timeout_s)
    if not observed.get("forwards"):
        return None, {"status": "unavailable",
                      "reason": "prefill_extraction_without_forwards",
                      "scan_counts": deepcopy(observed.get("scan_counts"))}
    return observed, {"status": "extracted",
                      "source_identity": deepcopy(observed.get("source_identity")),
                      "scan_counts": deepcopy(observed.get("scan_counts"))}


def _resolve_observation(raw, capture_path, observation, extraction_path,
                         context_offset, requested_context, expected_extraction,
                         extract_missing, max_rows, timeout_s):
    """Return (full observation or None, evidence, offset, offset basis)."""
    evidence = {"status": "not_provided",
                "reason": "scoped_observation_not_present"}
    observed = _observed_document(observation) if observation is not None else None
    if observed is not None and not has_layer_spans(observed):
        observed = None
        evidence = {"status": "unavailable",
                    "reason": "scoped_observation_has_no_complete_layer_spans"}
    if observed is None and extraction_path is not None:
        observed, evidence = load_verified_extraction(
            extraction_path, capture_path=capture_path,
            expected=expected_extraction)
    if (observed is None and extract_missing
            and evidence.get("status") in {"not_provided", "stale", "unavailable"}):
        observed, evidence = extract_full_observation(
            raw, capture_path, max_rows=max_rows, timeout_s=timeout_s)
    offset, basis = resolve_context_offset(
        observed, requested_context=requested_context,
        hardware_a5=is_a5_machine(raw), explicit=context_offset)
    return observed, evidence, offset, basis


def prepare_scoped_replay(raw, *, capture_path, observation=None,
                          extraction_path=None, expected_extraction=None,
                          requested_context=None, context_offset=None,
                          extract_missing=True, max_rows=MAX_SCAN_ROWS,
                          timeout_s=SCAN_TIMEOUT_S, archive_template=False):
    """Prepare one capture exactly once and return a releasable context."""
    observed, evidence, offset, basis = _resolve_observation(
        raw, capture_path, observation, extraction_path, context_offset,
        requested_context, expected_extraction, extract_missing, max_rows,
        timeout_s)
    prepared = prepare_scoped_capture(
        capture_path, observed, raw=raw, context_offset=offset,
        max_rows=max_rows, timeout_s=timeout_s)
    declared = (observed or {}).get("source_identity")
    source = prepared.source_before or {}
    if isinstance(declared, dict) and declared.get("sha256") and source.get("sha256"):
        evidence["source_hash_verified"] = declared["sha256"] == source["sha256"]
    return PreparedScopedReplay(
        prepared=prepared, capture_path=capture_path, observation=observed,
        observation_evidence=evidence, context_offset=offset,
        context_offset_basis=basis, archive_template=archive_template)


class PreparedScopedReplay:
    """One capture's reusable prepared evidence; apply one geometry at a time."""

    def __init__(self, *, prepared, capture_path, observation,
                 observation_evidence, context_offset, context_offset_basis,
                 archive_template=False):
        self._prepared = prepared
        self.capture_path = str(capture_path)
        self._observation = observation
        self.observation_evidence = deepcopy(observation_evidence)
        self.context_offset = context_offset
        self.context_offset_basis = context_offset_basis
        self.archive_template = bool(archive_template)

    def geometries(self):
        if self._prepared is None:
            raise ReleasedScopedReplay("prepared_scope_released")
        return self._prepared.geometries()

    def _scope_defaults(self, replace_recipe, archive_template):
        if self._prepared is None:
            raise ReleasedScopedReplay("prepared_scope_released")
        if archive_template is None:
            archive_template = self.archive_template
        if replace_recipe is None:
            replace_recipe = bool(archive_template)
        return replace_recipe, archive_template

    def apply_scope(self, raw: dict, *, phase: str, tokens: int, context: int,
                    sequences: int = 1, replace_recipe=None,
                    archive_template=None) -> tuple[dict, dict]:
        """Apply only the phase/geometry-scoped caller declaration."""
        replace_recipe, archive_template = self._scope_defaults(
            replace_recipe, archive_template)
        return self._prepared.apply(
            raw, phase=phase, tokens=tokens, context=context,
            sequences=sequences, replace_recipe=replace_recipe,
            archive_template=archive_template)

    def apply(self, raw: dict, *, phase: str, tokens: int, context: int,
              sequences: int = 1, replace_recipe=None,
              archive_template=None) -> tuple[dict, dict]:
        """Run the scoped caller on this geometry, then maintained native profiles."""
        scoped_raw, scope = self.apply_scope(
            raw, phase=phase, tokens=tokens, context=context,
            sequences=sequences, replace_recipe=replace_recipe,
            archive_template=archive_template)
        from native_observations import apply_native_observations

        geometry = dict(phase=phase, tokens=tokens, context=context,
                        sequences=sequences)
        declared_raw, native = apply_native_observations(scoped_raw, **geometry)
        prefill = native.get("prefill_native")
        if not isinstance(prefill, dict):
            candidates = [row for row in native.get("profiles", [])
                          if isinstance(row, dict)
                          and row.get("schema_version")
                          == "mindie-profiler-native-observation-import/1"]
            prefill = candidates[-1] if candidates else {}
        scope_status, scope_reason = scope.get("status"), scope.get("reason")
        evidence_status = self.observation_evidence.get("status")
        if evidence_status in {"stale", "unsupported"}:
            scope_status = "unsupported"
            scope_reason = ("scope_evidence_" + str(evidence_status) + ":"
                            + str(self.observation_evidence.get("reason")))
        status, reason = _combined_status(scope_status, prefill.get("status"))
        compact_scope = compact_scope_provenance(scope)
        if (compact_scope.get("observation_sha256") is None
                and self.observation_evidence.get("sha256")):
            compact_scope["observation_sha256"] = self.observation_evidence["sha256"]
        provenance = {
            "schema_version": SCHEMA,
            "status": status,
            "reason": reason,
            "geometry": geometry,
            "capture_path": self.capture_path,
            "context_offset": self.context_offset,
            "context_offset_basis": self.context_offset_basis,
            "observation_evidence": deepcopy(self.observation_evidence),
            "observation_forward_count": observation_forward_count(
                self._observation),
            "scope_status": scope_status,
            "scope_reason": scope_reason,
            "native_status": prefill.get("status"),
            "native_reason": prefill.get("reason"),
            "scope": compact_scope,
            "native": compact_native_provenance(prefill),
            "timing_values_used": False,
            "observations_modified": False,
            "source_paths_in_predictor_input": False,
        }
        return declared_raw, provenance

    def predict(self, raw: dict, *, phase: str, tokens: int, context: int,
                sequences: int = 1, replace_recipe=None,
                archive_template=None) -> dict:
        """Price the final adapted raw through the unchanged Body API."""
        from body import predict_body as _predict_body

        declared, provenance = self.apply(
            raw, phase=phase, tokens=tokens, context=context,
            sequences=sequences, replace_recipe=replace_recipe,
            archive_template=archive_template)
        predicted = _predict_body(
            declared, phase=phase, tokens=tokens, context=context,
            sequences=sequences)
        predicted["native_observation_provenance"] = provenance
        return predicted

    def release(self):
        """Drop prepared evidence and the observation after jobs materialise."""
        self._prepared = None
        self._observation = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.release()
        return False


def _combined_status(scope_status, native_status):
    scope_ok = scope_status == "applied"
    native_ok = native_status == "applied"
    if scope_status in {"conflict", "unsupported"}:
        return scope_status, "scope_evidence_conflict_or_unsupported"
    if scope_status in {"not_provided", "unbound", None} and native_status == "unsupported":
        return "unsupported", "native_observation_unsupported"
    if scope_ok and native_ok:
        return "applied", "scoped_caller_and_native_observations_applied"
    if scope_ok:
        return "applied_scope_only", "scoped_caller_applied_native_not_applicable"
    if native_ok:
        return "applied_native_only", "native_observations_applied_scope_unbound"
    return "unbound", "no_scoped_or_native_adaptation_applied"


def compact_scope_provenance(provenance):
    """Retain per-geometry decisions without the capture's whole geometry table."""
    provenance = provenance if isinstance(provenance, dict) else {}
    selection = provenance.get("selection") if isinstance(provenance.get("selection"), dict) else {}
    simulation = provenance.get("sim") if isinstance(provenance.get("sim"), dict) else {}
    source = provenance.get("source") if isinstance(provenance.get("source"), dict) else {}
    observation = provenance.get("observation") if isinstance(provenance.get("observation"), dict) else {}
    return {
        "schema_version": provenance.get("schema_version"),
        "status": provenance.get("status"),
        "reason": provenance.get("reason"),
        "source_sha256": source.get("sha256"),
        "source_size_bytes": source.get("size_bytes"),
        "observation_sha256": observation.get("sha256"),
        "context_offset": provenance.get("context_offset"),
        "caller": deepcopy(provenance.get("caller")),
        "declaration": deepcopy(provenance.get("declaration")),
        "selection": {
            "window_count": selection.get("window_count"),
            "witnesses": deepcopy(selection.get("witnesses")),
            "first_conflict": deepcopy(selection.get("first_conflict")),
        },
        "sim": {
            "supported": simulation.get("supported"),
            "reason": simulation.get("reason"),
            "mismatches": deepcopy(simulation.get("mismatches", []))[:8],
        },
        "applied_fields": deepcopy(provenance.get("applied_fields")),
        "preserved_conflicts": deepcopy(provenance.get("preserved_conflicts")),
        "unobserved": deepcopy(provenance.get("unobserved")),
    }


def compact_scope_sidecar(provenance):
    """Per-geometry status/provenance sidecar, including priceable declaration."""
    scope = provenance.get("scope") or {}
    native = provenance.get("native") or {}
    return {
        "geometry": provenance.get("geometry"),
        "status": provenance.get("status"),
        "reason": provenance.get("reason"),
        "scope_status": provenance.get("scope_status"),
        "scope_reason": provenance.get("scope_reason"),
        "native_status": provenance.get("native_status"),
        "native_reason": provenance.get("native_reason"),
        "context_offset": provenance.get("context_offset"),
        "declaration": (scope.get("declaration")
                        if provenance.get("scope_status") == "applied" else None),
        "source_sha256": scope.get("source_sha256"),
        "observation_sha256": scope.get("observation_sha256"),
        "native_profile": native.get("profile"),
        "native_imported_rule_count": native.get("imported_rule_count"),
        "timing_values_used": provenance.get("timing_values_used"),
    }


def compact_native_provenance(provenance):
    """Retain imported native counts/ids; measured tables stay in the sidecar."""
    provenance = provenance if isinstance(provenance, dict) else {}
    profile = provenance.get("profile") if isinstance(provenance.get("profile"), dict) else {}
    return {
        "schema_version": provenance.get("schema_version"),
        "status": provenance.get("status"),
        "reason": provenance.get("reason"),
        "profile": {"id": profile.get("id"), "sha256": profile.get("sha256")},
        "geometry": deepcopy(provenance.get("geometry")),
        "matched_domains": deepcopy(provenance.get("matched_domains")),
        "replaced_rule_ids": deepcopy(provenance.get("replaced_rule_ids")),
        "imported_rule_count": provenance.get("imported_rule_count"),
        "imported_rules": deepcopy(provenance.get("imported_rules")),
        "observations_modified": provenance.get("observations_modified"),
        "body_total_fitting": provenance.get("body_total_fitting"),
        "capture_binary_identity": provenance.get("capture_binary_identity"),
    }


def prediction_identity(raw, *, phase, tokens, context, sequences=1,
                        sim_identity, native_identity):
    """Identify one priceable input by its final physical raw and geometry.

    Capture paths, case names, observation values and timing selectors are not
    identity inputs. The two runtime identities keep stale predictions apart.
    """
    geometry = dict(phase=phase, tokens=tokens, context=context,
                    sequences=sequences)
    material = json.dumps({
        "schema": PREDICTION_SCHEMA,
        "sim_identity": sim_identity,
        "native_observation_identity": native_identity,
        "raw": raw,
        "geometry": geometry,
    }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(material.encode("utf-8")).hexdigest()


def prefill_geometries(observed, context_limit, *, context_offset=0):
    """Retain the observed per-forward prefill partition exactly.

    Explicit observed contexts are authoritative and never shifted; only a
    forward without one uses the retained context cursor, starting at the
    resolved A5 truncated-prefill offset. This keeps a mixed capture's tail
    chunk and an inferred first context distinct from a zero-based count.
    """
    forwards = (observed or {}).get("forwards") or []
    context, geometries = int(context_offset), []
    limit = int(context_limit)
    for forward in forwards:
        rows = int(forward["query_rows"])
        explicit = forward.get("context", forward.get("context_tokens"))
        if explicit is not None:
            context = int(explicit)
        else:
            context = 0 if (context > 0 and context + rows > limit) else context
        geometries.append({"tokens": rows, "context": context})
        context = context + rows
    return geometries


def validate_scope_plan(scope_plan, *, geometries, forward_count):
    """An explicit scope plan must describe exactly the observed partitions."""
    if scope_plan is None:
        return None
    signatures = scope_plan.get("signatures")
    if not isinstance(signatures, list):
        raise ValueError("scoped_plan_signatures_missing")
    if len(signatures) != forward_count or len(geometries) != forward_count:
        raise ValueError(
            "scoped_plan_geometry_count_mismatch:"
            f"{len(signatures)}!={forward_count}")
    for index, (signature, geometry) in enumerate(zip(signatures, geometries)):
        if (int(signature.get("tokens", -1)) != geometry["tokens"]
                or int(signature.get("context", -1)) != geometry["context"]):
            raise ValueError(f"scoped_plan_geometry_mismatch:{index}")
        if not signature.get("key"):
            raise ValueError(f"scoped_plan_key_missing:{index}")
    return signatures


def _atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".scoped-pred-", suffix=".json",
                                    dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, separators=(",", ":"), allow_nan=False)
            handle.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def read_prediction_cache(key, cache_root):
    path = Path(cache_root) / f"pred_{key}.json"
    if not path.is_file():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"corrupt_prediction_cache:{path}") from exc
    if cached.get("status") != "modeled":
        return None
    recorded = cached.get("prediction_identity")
    if recorded is not None and recorded != key:
        return None
    return cached


def price_declared_prediction(key, raw, *, phase, tokens, context,
                              sequences, cache_root, writer=None):
    """Price one final raw; the cache key is the final physical identity."""
    cached = read_prediction_cache(key, cache_root)
    if cached is not None:
        return cached
    from body import predict_body as _predict_body

    result = _predict_body(raw, phase=phase, tokens=tokens, context=context,
                           sequences=sequences)
    for field in ("parameters", "scheduled_operator_summary",
                  "native_observation_provenance"):
        result.pop(field, None)
    result["prediction_identity"] = key
    (writer or _atomic_write_json)(Path(cache_root) / f"pred_{key}.json",
                                   result)
    return result
