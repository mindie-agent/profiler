"""Direct score and the dataset entry keep the same source role.

The model fit flag stays false. The source sample keeps its own fit flag.
in_sample rows stay in the original denominator. Host captures are opt-in.
"""
from __future__ import annotations

import copy
import gzip
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import fleet_archive_case as archive_case  # noqa: E402
import fleet_capture_observations as observations  # noqa: E402
import fleet_operator_archive as archive  # noqa: E402
import fleet_operator_modeling as modeling  # noqa: E402
import hf_benchmark_gate as gate  # noqa: E402
import hf_profiling_benchmark as hf  # noqa: E402

EXTENDED = "extended_a3_a5_workstream_captures:a5/heldout_engine_20261031/a5_qwen30ba3b_tp4_ep4_decode_4k_c1"
WAVE = "wave5:a5:a5/a5_qwen30ba3b_tp4_ep4_decode:a5_qwen30ba3b_tp4_ep4_decode_4k_c1"
KIMI = "dsh_heldout:a3/heldout_engine_20261030/kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prof/prefill_c1_p16k/kernel_details.csv"
_ROLE = (
    "evaluation_relation", "calibration_role", "coverage_only", "target_timing_used_to_fit",
    "model_target_timing_used_to_fit", "slice_role_inherited", "slice_role_source_id",
    "key_denominator", "key_matched", "key_missing", "keys_over_10pct", "group_passed_10pct",
    "comparison",
)


def _fleet_path() -> Path:
    override = os.environ.get("MINDIE_FLEET_CAPTURES", "")
    if override:
        return Path(override)
    return Path("/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl")


def _opted_in(config: pytest.Config) -> bool:
    if os.environ.get("MINDIE_ARCHIVE_INTEGRATION") == "1":
        return True
    return "archive_integration" in str(config.option.markexpr or "")


def _row(capture_id: str, *, relation: str, fit: bool, coverage: bool, status: str,
         comparison: str, reason: str, denominator: int, matched: int, missing: int, over: int | None) -> dict:
    return {
        "capture_id": capture_id,
        "evaluation_relation": relation,
        "calibration_role": relation,
        "coverage_only": coverage,
        "target_timing_used_to_fit": fit,
        "model_target_timing_used_to_fit": False,
        "prediction_status": status,
        "comparison": comparison,
        "comparison_reason": reason,
        "boundary_scope": "forward_body",
        "key_denominator": denominator,
        "key_matched": matched,
        "key_missing": missing,
        "keys_over_10pct": over,
    }


def test_in_sample_row_stays_in_the_fixed_denominator() -> None:
    """Dropping the fitted row would shrink the original id count."""
    coverage = _row(
        "wave", relation="regime_table_replay", fit=True, coverage=True, status="modeled",
        comparison="invalid", reason="sample_key_population_mismatch",
        denominator=2, matched=1, missing=1, over=1,
    )
    holdout = _row(
        "hold", relation="template_matched_heldout_replay", fit=False, coverage=False, status="missing",
        comparison="uncovered", reason="", denominator=2, matched=0, missing=2, over=None,
    )
    source_only = _row(
        "src", relation="template_matched_heldout_replay", fit=False, coverage=False, status="source_only",
        comparison="uncovered", reason="source_only", denominator=1, matched=0, missing=1, over=None,
    )
    failed = _row(
        "bad", relation="template_matched_heldout_replay", fit=False, coverage=False, status="predictor_failed",
        comparison="invalid", reason="predictor_failed", denominator=1, matched=0, missing=1, over=None,
    )
    account = gate.all_original_account([coverage, holdout, source_only, failed])
    assert account["id_denominator"] == 4
    assert account["window_key_denominator"] == 6
    assert account["predictions"] == 1
    assert account["missing"] == 5
    assert account["over"] == 1
    assert account["within"] == 0
    assert account["strata"]["coverage"]["ids"] == 1
    assert account["strata"]["coverage"]["window_key_denominator"] == 2
    assert account["strata"]["independent_holdout"]["ids"] == 3
    assert account["strata"]["independent_holdout"]["within"] == 0
    assert account["unresolved"] == {"source_only": 1, "no_forecast": 1, "conditional": 1, "failed": 1}
    assert account["global_unresolved"] is True


def test_alias_pair_is_not_an_independent_holdout_pass() -> None:
    """Two within alias ids stay coverage. They are not two holdout passes."""
    def _alias(capture_id: str) -> dict:
        return _row(
            capture_id, relation="in_sample_regime_calibration", fit=True, coverage=True,
            status="modeled", comparison="compared", reason="", denominator=1, matched=1, missing=0, over=0,
        )
    account = gate.all_original_account([_alias("extended"), _alias("wave")])
    assert account["id_denominator"] == 2
    assert account["window_key_denominator"] == 2
    assert account["within"] == 2
    assert account["strata"]["coverage"]["ids"] == 2
    assert account["strata"]["coverage"]["within"] == 2
    assert account["strata"]["independent_holdout"]["ids"] == 0
    assert account["strata"]["independent_holdout"]["within"] == 0
    assert account["global_unresolved"] is False


def _load(ids: set[str]) -> dict[str, dict]:
    path = _fleet_path()
    if not path.is_file():
        pytest.skip(f"host fleet archive absent: {path}")
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("capture_id") in ids:
            found[row["capture_id"]] = row
    return found


def _publish_index0(row: dict) -> tuple[dict, dict]:
    archive_case.configure_archive_roots(receipt_index=None)
    cfg = gate.prediction_config(row)
    resolved = archive_case.resolve_archive_case(cfg)
    probe = modeling._archive_probe(resolved)
    published = archive.publish_archive_prediction(probe, cfg, material_indexes=(0,))
    observed = observations.extract_capture_observations(cfg)
    return published, observed


def _mini(root: Path, rows: list[dict]) -> Path:
    data = root / "data"
    data.mkdir(parents=True)
    fleet = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
    for name, blob in (("zero_shot_l1_l4_cells.jsonl", b""), ("fleet_captures.jsonl", fleet)):
        (data / name).write_bytes(blob)
        (data / f"{name}.gz").write_bytes(gzip.compress(blob, mtime=0))
    return root


def _shuffle_targets(observation: dict) -> dict:
    copied = copy.deepcopy(observation)
    window = copied["measurements"]["per_forward_window"]
    values = list(window.get("samples_ms") or [])
    assert len(values) == 139
    rotated = values[1:] + values[:1]
    assert rotated != values
    window["samples_ms"] = rotated
    return copied


@pytest.fixture
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")


@pytest.mark.archive_integration
def test_two_actual_captures_keep_source_roles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pytestconfig: pytest.Config, _isolate: None) -> None:
    """Index 0 is paired. The other 138 keys stay missing. Roles match the dataset entry."""
    if not _opted_in(pytestconfig):
        pytest.skip("archive integration is opt-in")
    modeling.clear_caches()
    rows = _load({EXTENDED, WAVE, KIMI})
    assert set(rows) == {EXTENDED, WAVE, KIMI}
    saved = {}
    observed = {}
    for capture_id in (EXTENDED, WAVE):
        saved[capture_id], observed[capture_id] = _publish_index0(rows[capture_id])
        assert saved[capture_id]["target_timing_used_to_fit"] is False
        assert len(saved[capture_id]["boundary_samples"]) == 1
    direct = {
        capture_id: gate.score_fleet_row(rows[capture_id], observed[capture_id], saved[capture_id])
        for capture_id in (EXTENDED, WAVE)
    }
    assert direct[EXTENDED]["evaluation_relation"] == "in_sample_regime_calibration"
    assert direct[WAVE]["evaluation_relation"] == "regime_table_replay"
    for item in direct.values():
        assert item["coverage_only"] is True
        assert item["target_timing_used_to_fit"] is True
        assert item["model_target_timing_used_to_fit"] is False
        assert item["slice_role_inherited"] is False
        assert item["slice_role_source_id"]
        assert item.get("attribution_mismatch") is not True
        assert item["key_denominator"] == 139
        assert item["key_matched"] == 1
        assert item["key_missing"] == 138
        assert item["keys_over_10pct"] == 1
        assert item["group_passed_10pct"] is False
        assert item["comparison"] == "invalid"
    assert direct[EXTENDED]["slice_role_source_id"] == direct[WAVE]["slice_role_source_id"]
    alone = {
        capture_id: gate.score_fleet_row(rows[capture_id], observed[capture_id], saved[capture_id])
        for capture_id in (EXTENDED, WAVE)
    }
    assert {item["evaluation_relation"] for item in alone.values()} == {
        "in_sample_regime_calibration", "regime_table_replay",
    }
    shuffled = gate.score_fleet_row(rows[WAVE], _shuffle_targets(observed[WAVE]), saved[WAVE])
    for key in _ROLE:
        if key in {"key_matched", "key_missing", "keys_over_10pct", "group_passed_10pct", "comparison"}:
            continue
        assert shuffled[key] == direct[WAVE][key]
    assert shuffled["key_denominator"] == 139
    assert shuffled["evaluation_relation"] == "regime_table_replay"
    kimi_obs = observations.extract_capture_observations(gate.prediction_config(rows[KIMI]))
    kimi = gate.score_fleet_row(rows[KIMI], kimi_obs, {})
    assert kimi["evaluation_relation"] == "template_matched_heldout_replay"
    assert kimi["coverage_only"] is False
    assert kimi["target_timing_used_to_fit"] is False
    assert kimi["model_target_timing_used_to_fit"] is None
    assert kimi["slice_role_source_id"] != direct[WAVE]["slice_role_source_id"]
    assert kimi["key_matched"] == 0
    assert kimi["key_missing"] == kimi["key_denominator"]
    account = gate.all_original_account([direct[EXTENDED], direct[WAVE], kimi])
    assert account["id_denominator"] == 3
    assert account["strata"]["coverage"]["ids"] == 2
    assert account["strata"]["independent_holdout"]["ids"] == 1
    assert account["strata"]["independent_holdout"]["within"] == 0
    assert account["strata"]["coverage"]["predictions"] == 2
    assert account["strata"]["coverage"]["missing"] == 276
    assert account["global_unresolved"] is True

    def _frozen(cfg: dict) -> dict:
        return saved[cfg["capture_id"]]

    monkeypatch.setattr(hf, "predict_capture_operators_and_step", _frozen)
    summary = hf.evaluate_dataset(_mini(tmp_path / "ds", [rows[EXTENDED], rows[WAVE]]), summary_dir=tmp_path / "out")
    exported = [json.loads(line) for line in (tmp_path / "out" / "per_id.jsonl").read_text(encoding="utf-8").splitlines()]
    by_id = {item["capture_id"]: item for item in exported}
    assert set(by_id) == {EXTENDED, WAVE}
    for capture_id, item in by_id.items():
        for key in _ROLE:
            assert item.get(key) == direct[capture_id][key]
    original = summary["all_original"]
    assert original["id_denominator"] == 2
    assert original["window_key_denominator"] == 278
    assert original["predictions"] == 2
    assert original["missing"] == 276
    assert original["over"] == 2
    assert original["within"] == 0
    assert original["strata"]["coverage"]["ids"] == 2
    assert original["strata"]["independent_holdout"]["ids"] == 0
    assert summary["strict_global_pass"] is False
