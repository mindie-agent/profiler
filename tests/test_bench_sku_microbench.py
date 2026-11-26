"""L0 preset plan emission, arch-gated dtypes, observations journal, and CLI alias tests.

[Role]
  Verify pure-data ``l0_presets`` plan generation (all five domains, A2/A3 FP8
  refusal vs A5 FP8/MXFP8/MXFP4 enablement, integer ``group_list`` token
  conservation, ``bench sku --dry-run`` portability) and ``ObservationJournal``
  integrity (identities, bounded tail repair, incomplete-case purge).

[Invariants]
  * Native FP8/MXFP8/MXFP4/HiF8 is refused on A2/A3 and permitted on A5.
  * Every ``group_list`` is an integer list that conserves tokens.
  * Over-budget and unavailable-builder cases never fabricate durations.

[Timeouts & Locks]
  Pure in-memory work plus bounded file I/O under ``tmp_path``.

[Side-Effect Policy]
  Writes only under pytest ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mindie_profiler.bench import campaign_runner, env_fingerprint, l0_presets
from mindie_profiler.bench.campaign_store import PLAN_V2_SCHEMA, verify_seal
from mindie_profiler.bench.observations import (
    IDENTITY_FIELDS,
    ObservationJournal,
    observation_row,
)
from mindie_profiler.bench.subgraph_runtime import OperatorExecutor
from mindie_profiler.events import ProfilerUsageError
from tests.test_bench_operators import FakeBackend


class _FixedProtocol:
    repeats = 2

    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, enqueue, *, case_id, **_kwargs):
        self.calls.append(case_id)
        enqueue()
        return {
            "schema": "mindie-bench-timing/1",
            "case_id": case_id,
            "protocol": "warmups + trials x repeats device events",
            "timer_source": "torch.npu.Event(enable_timing=True)",
            "minimum_ms": 0.001,
            "startup_ms": 0.0,
            "qualified": True,
            "modes": {
                "eager": {
                    "qualified": True,
                    "median_us": 1.0,
                    "p50_us": 1.0,
                    "p90_us": 1.2,
                    "p99_us": 1.3,
                    "min_us": 0.9,
                    "iqr_us": 0.1,
                    "cv_pct": 1.0,
                    "trials": [{"trial": 0, "repeats_us": [1.0, 1.2]}],
                },
            },
        }


def test_l0_plan_covers_all_l0_domains_with_unique_ids_and_valid_seal():
    plan = l0_presets.build_l0_plan(sku=l0_presets.DAV_2201)
    assert plan["schema"] == PLAN_V2_SCHEMA
    assert verify_seal(plan, "plan_sha256") is True
    cases = plan["cases"]
    assert {case["identities"]["domain"] for case in cases} == set(l0_presets.DOMAIN_IDS) == {1, 2, 3, 5}
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids))
    assert all(cid.startswith("k2-") for cid in ids)
    for case in cases:
        assert case["split"] in {"train", "heldout"}
        assert case["canonical_key"]["sig_version"] == 2


def test_native_fp8_refused_on_a2_a3_and_enabled_on_a5():
    for dtype in ("fp8", "fp8_e4m3", "mxfp8", "mxfp4", "hif8"):
        with pytest.raises(ProfilerUsageError, match="bench_native_fp8_unsupported"):
            l0_presets.build_l0_plan(sku=l0_presets.DAV_2201, dtypes=[dtype])
        with pytest.raises(ProfilerUsageError, match="bench_native_fp8_unsupported"):
            l0_presets.build_l0_plan(sku="Ascend910_9362", dtypes=[dtype])

    a5_plan = l0_presets.build_l0_plan(
        sku="Ascend950DT_9581", domains=[2], dtypes=["fp8_e4m3", "mxfp8", "mxfp4"],
    )
    assert verify_seal(a5_plan, "plan_sha256") is True
    assert {c["canonical_key"]["dtypes"]["input"] for c in a5_plan["cases"]} == {
        "fp8_e4m3", "mxfp8", "mxfp4",
    }

    with pytest.raises(ProfilerUsageError, match="bench_sku_unsupported"):
        l0_presets.build_l0_plan(sku="DAV_3510")
    with pytest.raises(ProfilerUsageError, match="bench_dtype_unsupported"):
        l0_presets.build_l0_plan(dtypes=["fp32"])
    with pytest.raises(ProfilerUsageError, match="bench_domain_unknown"):
        l0_presets.build_l0_plan(domains=[9])


def test_uniform_and_zipf_histograms_conserve_tokens():
    assert l0_presets.uniform_counts(8, 10) == [2, 2, 1, 1, 1, 1, 1, 1]
    assert sum(l0_presets.zipf_counts(32, 4096)) == 4096
    counts = l0_presets.zipf_counts(16, 1024)
    assert counts == sorted(counts, reverse=True)
    assert len(l0_presets.zipf_counts(16, 1024, exponent=1.2)) == 16


def test_domain3_group_lists_are_integers_conserving_tokens():
    plan = l0_presets.build_l0_plan(domains=[3], dtypes=["bf16"])
    assert plan["cases"]
    for case in plan["cases"]:
        group = case["canonical_key"]["per_expert_token_counts"]
        assert isinstance(group, list) and group
        assert all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in group)
        assert sum(group) == case["canonical_key"]["canonical_shapes"]["m"]


def test_cli_sku_dry_run_emits_portable_plan_without_torch(capsys):
    assert campaign_runner.main_sku(["--dry-run", "--domain", "2", "--dtype", "bf16"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["sku"] == l0_presets.DAV_2201
    assert payload["case_count"] > 0
    text = json.dumps(payload)
    assert "/dev/davinci" not in text and "@sha256:" not in text

    assert campaign_runner.main_sku(["--dry-run", "--limit", "3"]) == 0
    limited = json.loads(capsys.readouterr().out)
    assert limited["case_count"] == 3


def test_over_budget_and_unavailable_builder_never_fabricate_durations(tmp_path):
    plan = l0_presets.build_l0_plan(sku=l0_presets.DAV_2201, domains=[2], dtypes=["bf16"])
    one_case_plan = {
        **plan,
        "cases": [plan["cases"][0]],
    }
    one_case_plan.pop("plan_sha256", None)

    class FailIfRun:
        def run(self, *_args, **_kwargs):
            raise AssertionError("over-budget case was executed")

    backend = FakeBackend()
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku=l0_presets.DAV_2201, soc_arch="A2", observed_clock_mhz=1650.0, clock_source="test",
    )
    manifest = campaign_runner.run_campaign(
        one_case_plan,
        campaign_dir=tmp_path / "budget-camp",
        env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context(budget={"cap_bytes": 1024})),
        protocol=FailIfRun(),
    )
    assert manifest["cases"] == []
    assert len(manifest["blocked_cases"]) == 1
    assert manifest["blocked_cases"][0]["status"] == "over_budget"
    assert manifest["blocked_cases"][0]["measured_ns"] is None
    assert manifest["blocked_cases"][0]["stats_us"] is None


def test_campaign_runner_incremental_resume_skips_completed_cases(tmp_path):
    plan = l0_presets.build_l0_plan(sku=l0_presets.DAV_2201, domains=[1], dtypes=["bf16"])
    subset = {**plan, "cases": [c for c in plan["cases"] if c["canonical_key"]["bench_builder"] == "rms_norm"][:1]}
    subset.pop("plan_sha256", None)
    backend = FakeBackend()
    protocol = _FixedProtocol()
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku=l0_presets.DAV_2201, soc_arch="A2", observed_clock_mhz=1650.0, clock_source="test",
    )
    camp_dir = tmp_path / "inc-camp"
    first = campaign_runner.run_campaign(
        subset,
        campaign_dir=camp_dir,
        env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=protocol,
        l2_bytes=1024,
        run_id="run-1",
    )
    assert first["executed_case_count"] == 1 and first["cache_hit_count"] == 0
    assert first["cases"][0]["qualified"] is True
    second = campaign_runner.run_campaign(
        subset,
        campaign_dir=camp_dir,
        env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=protocol,
        l2_bytes=1024,
        run_id="run-2",
    )
    assert second["executed_case_count"] == 0 and second["cache_hit_count"] == 1
    assert second["cases"][0]["cache_status"] == "hit"
    assert second["cases"][0]["measured_in_run_id"] == "run-1"
    assert len(protocol.calls) == 1


def test_observation_row_applies_plan_identities_and_execution_mode():
    case = {"case_id": "d1.empty.event_pair", "split": "train"}
    accuracy = {field: field for field in IDENTITY_FIELDS}
    accuracy["execution"] = {"mode": "eager", "stage": "s0_local"}
    row = observation_row(
        plan_id="plan-1", case=case, run_id="run-1", split="train",
        boundary="device_kernel", timing_mode="aclgraph", residency="device",
        trial=0, repeat_index=1, rank=None, duration_ms=1.0,
        source="capture://bench/row", identity_override=accuracy,
        service_identity={"resource": "cube", "work_unit": "flops"},
    )
    assert row["identity"]["hardware"] == "hardware"
    assert row["identity"]["execution"] == {"mode": "aclgraph", "stage": "s0_local"}
    assert row["service_identity"] == {"resource": "cube", "work_unit": "flops"}
    assert accuracy["execution"]["mode"] == "eager"
    partial = observation_row(
        plan_id="plan-1", case=case, run_id="run-1", split="train",
        boundary="device_kernel", timing_mode="eager", residency="device",
        trial=0, repeat_index=0, rank=None, duration_ms=1.0,
        source="capture://bench/row", identity_override={"level": "operator"},
    )
    assert set(partial["identity"]) == set(IDENTITY_FIELDS)
    assert "service_identity" not in partial


def test_observation_journal_repairs_a_torn_tail_before_appending(tmp_path):
    path = tmp_path / "journal.jsonl"
    journal = ObservationJournal(path)
    journal.append({"record_type": "observation", "case_id": "a", "run_id": "r"})
    assert journal.repair() == 0
    with path.open("ab") as handle:
        handle.write(b'{"record_type": "observation", "case_id": "torn"')
    journal.append({"record_type": "observation", "case_id": "b", "run_id": "r"})
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert [line["case_id"] for line in lines] == ["a", "b"]
    assert journal.repair() == 0


def test_observation_journal_tail_repair_is_bounded_on_a_valid_file(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    journal = ObservationJournal(path)
    journal.append({
        "record_type": "case_complete", "case_id": "a", "run_id": "r", "status": "ok",
    })
    assert journal.completed_keys() == {(None, "a")}

    def forbidden(self):
        raise AssertionError("tail repair read the whole journal")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    assert journal.repair() == 0
    journal.append({"record_type": "observation", "case_id": "b", "run_id": "r"})
    assert [json.loads(line)["case_id"] for line in path.read_text().splitlines()] == ["a", "b"]


def test_purge_incomplete_cases_drops_only_uncommitted_rows(tmp_path):
    journal = ObservationJournal(tmp_path / "journal.jsonl")
    journal.append({"record_type": "observation", "case_id": "done", "sku": "s", "run_id": "r", "status": "ok"})
    journal.append({"record_type": "case_complete", "case_id": "done", "sku": "s", "run_id": "r", "status": "ok"})
    journal.append({"record_type": "observation", "case_id": "torn", "sku": "s", "run_id": "r", "status": "ok"})
    assert journal.purge_incomplete_cases() == 1
    assert journal.purge_incomplete_cases() == 0
    rows = [json.loads(line) for line in journal.path.read_text().splitlines()]
    assert [row["case_id"] for row in rows] == ["done", "done"]
    assert journal.completed_keys() == {("s", "done")}


def test_kernel_class_participates_in_the_observation_identity_shape():
    row = observation_row(
        plan_id="p",
        case={"case_id": "d2.mte2", "kernel_class": "aic", "shape": {"bytes": 4096}},
        run_id="r", split="train", boundary="device_kernel",
        timing_mode="eager", residency="dram", trial=0, repeat_index=0,
        rank=None, duration_ms=1.0, source="capture://bench/row",
    )
    assert row["identity"]["shape"]["kernel_class"] == "aic"
    assert row["key"]["shape"]["kernel_class"] == "aic"
