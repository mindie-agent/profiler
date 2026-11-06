"""Explicit qualification of retained Wave 5 calibration declarations.

[Role] Reject known capture-selected A3 AllReduce responses, then bind legacy
  Kimi HCCL declarations to the transport in maintained source cases.
[Invariants] Rejection requires the exact retained physical payload. Foreign
  responses remain caller declarations. Retained response values and all source
  files/observations stay unchanged; ordinary analytic predictions stay scored.
[Timeouts & Locks] Local JSON reads and bounded four-layer source graph creation;
  no subprocesses, network, locks or fitting.
[Side-Effect Policy] Returns an in-memory catalog and hashed provenance. Never
  writes the archive, source cases, captures or simulator state.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from mindie_sim import target_operators
from mindie_sim.prediction.services import service_identity
from mindie_sim.prediction.structure import parse_case

from prefill_native_observations import PROFILE_PATH


_CASES = Path(__file__).resolve().parent / "cases"
_REFERENCES = tuple(_CASES / f"a3-kimi4-tp{tp}-longctx-source.json" for tp in (8, 16))
_LEGACY_FIELDS = frozenset({"links", "placements", "ranks_per_node", "dies_per_package"})
_RULE_FIELDS = ("id", "match", "coordinates", "domain", "response", "execution")


def _read_source(path: Path) -> tuple[dict, dict]:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return json.loads(path.read_text(encoding="utf-8")), {
        "path": str(path.resolve()), "sha256": digest.hexdigest(),
    }


def _source_transports(raw: dict) -> dict[str, dict]:
    case = parse_case(raw)
    identities = {}
    for op in target_operators(raw, phase="decode", tokens=1, context=0, sequences=1):
        if op.recipe != "hccl_entry":
            continue
        identity = service_identity(case, op, "full")
        implementation = identity["implementation"]
        transport = identity["transport"]
        if implementation in identities and identities[implementation] != transport:
            raise ValueError(f"ambiguous_source_transport:{implementation}")
        identities[implementation] = transport
    return identities


def _rule_payload(rule: dict) -> str:
    return json.dumps({name: rule.get(name) for name in _RULE_FIELDS},
                      sort_keys=True, separators=(",", ":"), allow_nan=False)


def _reject_capture_selected_responses(catalog: dict) -> dict:
    """Reject the enumerated archive responses, not arbitrary caller rules.

    The old catalog selects these phase/family-only constants by capture cohort,
    requested context and concurrency. They are not a transferable AllReduce
    service. The native profile already enumerates their exact physical variants;
    its replacement remains independently subject to its own physical domain.
    """
    profile, source = _read_source(PROFILE_PATH)
    known = {_rule_payload(rule) for rule in profile["replaced_regime_contracts"]}
    rejected = []
    for key, entry in catalog.items():
        retained = []
        for rule in entry["service_regimes"]:
            if _rule_payload(rule) in known:
                rejected.append({
                    "key": key, "cohort_file": entry["cohort_file"],
                    "rule": rule,
                })
            else:
                retained.append(rule)
        entry["service_regimes"] = retained
    return {
        "status": "rejected_calibration" if rejected else "unchanged",
        "reason": "historical_capture_selected_allreduce_response_has_no_physical_call_domain"
        if rejected else "no_known_unqualified_archive_response",
        "contract_source": source,
        "rejected_rule_count": len(rejected),
        "rejected_rules": rejected,
        "prediction_policy": "ordinary_analytic_recipe_remains_scored",
        "observations_modified": False,
        "replacement_response_fitted": False,
    }


def import_a3_regime_catalog(
    archive_root: Path, *, reference_paths: tuple[Path, ...] | None = None,
) -> tuple[dict, dict]:
    """Return a qualified catalog plus rejection and transport provenance.

    An already current declaration is unchanged. A legacy declaration must have
    exactly the four historical physical fields and equal the maintained rule
    on every existing identity field; conflicting declarations fail the import.
    """
    templates_dir = Path(archive_root) / "a3" / "templates"
    catalog, catalog_source = _read_source(templates_dir / "_regime_catalog.json")
    rejection = _reject_capture_selected_responses(catalog)
    references, reference_sources = {}, []
    for path in _REFERENCES if reference_paths is None else reference_paths:
        raw, source = _read_source(Path(path))
        reference_sources.append(source)
        transports = _source_transports(raw)
        for rule in raw["runtime"]["kernels"]["service_regimes"]:
            match = rule["match"]
            if "transport" not in match:
                continue
            implementation = match["implementation"]
            if match["transport"] != transports.get(implementation):
                raise ValueError(f"reference_transport_mismatch:{path}:{rule['id']}")
            if rule["id"] in references:
                raise ValueError(f"duplicate_reference_regime:{rule['id']}")
            references[rule["id"]] = match

    cohort_transports, cohort_sources, changes = {}, {}, []
    for key, entry in catalog.items():
        changed_rules = []
        for rule in entry["service_regimes"]:
            reference = references.get(rule["id"])
            if reference is None:
                continue
            match = rule["match"]
            rest = {name: value for name, value in match.items() if name != "transport"}
            expected_rest = {name: value for name, value in reference.items() if name != "transport"}
            if rest != expected_rest:
                raise ValueError(f"catalog_identity_conflict:{key}:{rule['id']}")
            old, current = match.get("transport", {}), reference["transport"]
            if old != current and (
                set(old) != _LEGACY_FIELDS or any(old[name] != current[name] for name in old)
            ):
                raise ValueError(f"catalog_transport_conflict:{key}:{rule['id']}")
            cohort_file = entry["cohort_file"]
            if cohort_file not in cohort_transports:
                raw, source = _read_source(templates_dir / cohort_file)
                cohort_sources[cohort_file] = source
                cohort_transports[cohort_file] = _source_transports(raw)
            if cohort_transports[cohort_file].get(match["implementation"]) != current:
                raise ValueError(f"cohort_transport_mismatch:{key}:{rule['id']}")
            if old == current:
                continue
            match["transport"] = deepcopy(current)
            changed_rules.append({
                "id": rule["id"],
                "added_transport_fields": sorted(set(current) - set(old)),
            })
        if changed_rules:
            changes.append({"key": key, "cohort_file": entry["cohort_file"], "rules": changed_rules})

    provenance = {
        "schema_version": "mindie-wave5-regime-import/1",
        "operation": "qualify_retained_calibration_and_transport_identity",
        "catalog": catalog_source,
        "reference_cases": reference_sources,
        "cohort_templates": [cohort_sources[name] for name in sorted(cohort_sources)],
        "changed_entries": changes,
        "changed_rule_count": sum(len(entry["rules"]) for entry in changes),
        "rejected_calibration": rejection,
        "responses_modified": False,
        "observations_modified": False,
        "imported_catalog_sha256": sha256(json.dumps(
            catalog, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest(),
    }
    return catalog, provenance
