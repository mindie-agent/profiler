"""Exercise explicit catalog imports against retained source declarations.

[Role] Reject unqualified archive responses and import transport identities.
[Invariants] Foreign responses and historical files survive; conflicts fail.
[Timeouts & Locks] Local four-layer source graphs, no remote operations.
[Side-Effect Policy] Catalog fixtures and all runtime homes live under tmp_path.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

STRUCT_DIR = Path(__file__).resolve().parents[1] / "examples" / "structure"
sys.path.insert(0, str(STRUCT_DIR))
from wave5_regime_import import import_a3_regime_catalog
from prefill_native_observations import PROFILE_PATH, apply_prefill_native_observations


def _archive(tmp_path, tp=8):
    reference = STRUCT_DIR / "cases" / f"a3-kimi4-tp{tp}-longctx-source.json"
    raw = json.loads(reference.read_text())
    regimes = deepcopy(raw["runtime"]["kernels"]["service_regimes"])
    for rule in regimes:
        if "transport" in rule["match"]:
            rule["match"]["transport"] = {
                name: value for name, value in rule["match"]["transport"].items()
                if name in {"links", "placements", "ranks_per_node", "dies_per_package"}
            }
    entry = {"cohort_file": "cohort.json", "tpl_name": "retained-kimi",
             "service_regimes": regimes, "seg_opts": {}, "cross_tp": False}
    catalog = {"cohort:196608:1": entry}
    templates = tmp_path / "a3" / "templates"
    templates.mkdir(parents=True)
    catalog_path = templates / "_regime_catalog.json"
    catalog_path.write_text(json.dumps(catalog))
    (templates / "cohort.json").write_text(json.dumps(raw))
    return reference, catalog_path, catalog


@pytest.mark.parametrize("tp", (8, 16))
def test_catalog_import_preserves_response_and_source_bytes(tmp_path, tp):
    reference, catalog_path, original = _archive(tmp_path, tp)
    original_bytes = catalog_path.read_bytes()
    imported, provenance = import_a3_regime_catalog(tmp_path, reference_paths=(reference,))
    current = json.loads(reference.read_text())["runtime"]["kernels"]["service_regimes"]
    assert imported["cohort:196608:1"]["service_regimes"] == current
    assert catalog_path.read_bytes() == original_bytes
    assert provenance["catalog"]["sha256"] == sha256(original_bytes).hexdigest()
    assert provenance["changed_rule_count"] == 2
    assert provenance["changed_entries"][0]["key"] == "cohort:196608:1"
    assert not provenance["responses_modified"] and not provenance["observations_modified"]
    for before, after in zip(original["cohort:196608:1"]["service_regimes"], current):
        assert {k: v for k, v in before.items() if k != "match"} == {
            k: v for k, v in after.items() if k != "match"
        }
    catalog_path.write_text(json.dumps(imported))
    again, unchanged = import_a3_regime_catalog(tmp_path, reference_paths=(reference,))
    assert again == imported
    assert unchanged["changed_entries"] == []


@pytest.mark.parametrize("conflict", ("implementation", "link", "parallel", "cohort"))
def test_catalog_import_rejects_conflicting_source_identity(tmp_path, conflict):
    reference, catalog_path, catalog = _archive(tmp_path)
    rule = next(row for row in catalog["cohort:196608:1"]["service_regimes"]
                if "transport" in row["match"])
    if conflict == "implementation":
        rule["match"]["implementation"] = "other-native-program"
    elif conflict == "link":
        rule["match"]["transport"]["links"][0]["capacity_bytes_per_ms"] *= 2
    elif conflict == "parallel":
        rule["match"]["transport"]["parallel"] = {"tp": 4}
    else:
        source = catalog_path.parent / "cohort.json"
        raw = json.loads(source.read_text())
        raw["runtime"].update(tp=4, ep=4)
        source.write_text(json.dumps(raw))
    catalog_path.write_text(json.dumps(catalog))
    original_bytes = catalog_path.read_bytes()
    with pytest.raises(ValueError, match="(identity_conflict|transport_conflict|transport_mismatch)"):
        import_a3_regime_catalog(tmp_path, reference_paths=(reference,))
    assert catalog_path.read_bytes() == original_bytes


def _write_catalog(root, catalog):
    path = root / "a3" / "templates" / "_regime_catalog.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(catalog), encoding="utf-8")
    return path


def _entry(rules):
    return {"cohort_file": "retained-qwen35.json", "service_regimes": rules,
            "tpl_name": "retained-qwen35", "seg_opts": {}, "cross_tp": False}


def test_catalog_rejects_exact_capture_responses_and_preserves_foreign_rules(tmp_path):
    contracts = json.loads(PROFILE_PATH.read_text())["replaced_regime_contracts"]
    catalog = {f"legacy:{i}": _entry([deepcopy(rule)])
               for i, rule in enumerate(contracts)}
    controls = []
    for field, value in (
        ("id", "caller_explicit_allreduce"),
        ("match", {"phase": "prefill", "family": "allgather"}),
        ("response", {"fixed_us": 123.456}),
        ("domain", {"rows": {"min": 8064, "max": 8064}}),
        ("execution", {"kind": "resource_service", "resource": "link"}),
    ):
        rule = deepcopy(contracts[0])
        rule[field] = value
        controls.append(rule)
        catalog[f"foreign:{field}"] = _entry([rule])
    path = _write_catalog(tmp_path, catalog)
    original = path.read_bytes()
    imported, provenance = import_a3_regime_catalog(tmp_path, reference_paths=())
    assert all(not imported[f"legacy:{i}"]["service_regimes"]
               for i in range(len(contracts)))
    assert [imported[key]["service_regimes"][0] for key in imported
            if key.startswith("foreign:")] == controls
    rejection = provenance["rejected_calibration"]
    assert rejection["status"] == "rejected_calibration"
    assert rejection["rejected_rule_count"] == len(contracts)
    assert [row["rule"] for row in rejection["rejected_rules"]] == contracts
    assert rejection["prediction_policy"] == "ordinary_analytic_recipe_remains_scored"
    assert not rejection["observations_modified"]
    assert not rejection["replacement_response_fitted"]
    assert path.read_bytes() == original
    path.write_text(json.dumps(imported), encoding="utf-8")
    again, unchanged = import_a3_regime_catalog(tmp_path, reference_paths=())
    assert again == imported
    assert unchanged["rejected_calibration"]["status"] == "unchanged"


def test_archive_qualification_preserves_native_domain_and_scores_short_chunks(tmp_path):
    from mindie_sim import predict

    fixture = Path(__file__).parent / "fixtures/native_observations/a3_qwen35_prefill_400k_native.json"
    original = json.loads(fixture.read_text())["raw_case"]
    path = _write_catalog(tmp_path, {
        "qwen35": _entry(original["runtime"]["kernels"]["service_regimes"]),
    })
    imported, provenance = import_a3_regime_catalog(tmp_path, reference_paths=())
    clean = deepcopy(original)
    clean["runtime"]["kernels"]["service_regimes"] = imported["qwen35"]["service_regimes"]
    geometry = dict(phase="prefill", tokens=8064, context=201600, sequences=1)
    before, before_meta = apply_prefill_native_observations(original, **geometry)
    after, after_meta = apply_prefill_native_observations(clean, **geometry)
    assert before_meta["status"] == after_meta["status"] == "applied"
    assert before == after
    assert provenance["rejected_calibration"]["rejected_rule_count"] == 1

    # The archived 4K synthetic source has eight layers. A short tail must not
    # inherit a context-selected constant when the native profile cannot apply.
    short = deepcopy(clean)
    short["model"]["layers"] = 8
    short["model"]["layer_plans"] = short["model"]["layer_plans"][:8]
    geometry = dict(phase="prefill", tokens=256, context=3840, sequences=1)
    adapted, native = apply_prefill_native_observations(short, **geometry)
    assert native["status"] == "not_applicable"
    result = predict(adapted, scope="body", **geometry, event_limit=0)
    reductions = [row for row in result["timeline"] if row["family"] == "allreduce"]
    assert len(reductions) == 16
    assert all(row["elapsed_ms"] < 92.0 for row in reductions)
    assert result["body_forward_ms"] > 0
    assert json.loads(path.read_text())["qwen35"]["service_regimes"] == original["runtime"]["kernels"]["service_regimes"]
