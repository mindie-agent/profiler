"""Exercise explicit catalog imports against retained source declarations.

[Role] Preserve archived responses while importing current transport identities.
[Invariants] Conflicts fail; historical files and non-transport fields survive.
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
