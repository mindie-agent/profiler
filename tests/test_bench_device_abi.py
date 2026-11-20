"""Standalone bench ABI admission: LOCAL_RANK-first bind, allowlist, receipts.

[Role]
  Verify that the bench binds the launcher-named ordinal before any device
  query, fails closed on a physical-die allowlist mismatch, enforces the S0
  VRAM envelope, reports absent device facts as ``None``, inspects installed
  operator schemas and canaries, and publishes only portable receipts.

[Invariants]
  * No test touches an NPU; every device surface is an explicit fake.
  * A physical-id guard never degrades into an allow-all when it cannot resolve.

[Timeouts & Locks]
  Pure in-memory work; no timers, threads or processes.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mindie_profiler.bench import abi
from mindie_profiler.events import ProfilerUsageError


class FakeNpu:
    """Minimal torch.npu surface: records every call it receives."""

    def __init__(self, *, free=24 * abi.GIB, total=64 * abi.GIB, properties=None):
        self.calls: list[str] = []
        self.ordinal: int | None = None
        self._free = free
        self._total = total
        self._properties = properties

    def set_device(self, ordinal):
        self.calls.append(f"set_device:{ordinal}")
        self.ordinal = int(ordinal)

    def device_count(self):  # pragma: no cover - must never be called
        self.calls.append("device_count")
        return 8

    def mem_get_info(self):
        self.calls.append("mem_get_info")
        return (self._free, self._total)

    def get_device_properties(self, ordinal):
        self.calls.append(f"get_device_properties:{ordinal}")
        return self._properties


class FakeTorch:
    def __init__(self, npu):
        self.npu = npu


def _torch(free=24 * abi.GIB):
    npu = FakeNpu(free=free)
    torch = FakeTorch(npu)
    return torch, npu


def test_local_rank_is_read_before_any_device_query():
    environ = {abi.LOCAL_RANK_ENV: "3"}
    torch, npu = _torch()
    receipt = abi.bind_device(torch=torch, torch_npu=npu, environ=environ,
                              allowed_phy_ids=(), resolver=lambda ordinal: 13)
    assert receipt["ordinal"] == 3
    assert npu.calls[0] == "set_device:3"
    assert "device_count" not in npu.calls
    assert receipt["physical_id"] == 13


def test_missing_local_rank_is_a_usage_error_not_a_device_count():
    torch, npu = _torch()
    with pytest.raises(ProfilerUsageError, match="bench_device_rank_missing"):
        abi.bind_device(torch=torch, torch_npu=npu, environ={}, allowed_phy_ids=())
    assert npu.calls == []


def test_local_rank_rejects_non_integer_and_out_of_range():
    for raw in ("", "abc", "-1", str(abi.MAX_DEVICE_ORDINAL + 1)):
        with pytest.raises(ProfilerUsageError):
            abi.resolve_local_rank({abi.LOCAL_RANK_ENV: raw})


def test_physical_allowlist_accepts_only_listed_die_and_records_it():
    environ = {abi.LOCAL_RANK_ENV: "2"}
    torch, npu = _torch()
    receipt = abi.bind_device(torch=torch, torch_npu=npu, environ=environ,
                              allowed_phy_ids=(12, 13, 14, 15),
                              resolver=lambda ordinal: 14)
    assert receipt["physical_id"] == 14
    assert receipt["allowed"] is True
    assert receipt["allowed_phy_ids"] == [12, 13, 14, 15]
    assert receipt["verified"] is True


def test_physical_allowlist_is_fail_closed_on_mismatch_and_unresolvable():
    environ = {abi.LOCAL_RANK_ENV: "0"}
    torch, npu = _torch()
    with pytest.raises(ProfilerUsageError, match="bench_physical_die_not_allowed"):
        abi.bind_device(torch=torch, torch_npu=npu, environ=environ,
                        allowed_phy_ids=(12, 13), resolver=lambda ordinal: 4)
    with pytest.raises(ProfilerUsageError, match="bench_physical_die_unverifiable"):
        abi.bind_device(torch=torch, torch_npu=npu, environ=environ,
                        allowed_phy_ids=(12,), resolver=lambda ordinal: None)


def test_visible_device_mask_must_contain_local_rank():
    torch, npu = _torch()
    with pytest.raises(ProfilerUsageError, match="bench_visible_device_mismatch"):
        abi.bind_device(torch=torch, torch_npu=npu,
                        environ={abi.LOCAL_RANK_ENV: "2",
                                 abi.VISIBLE_DEVICES_ENV: "0,1"},
                        allowed_phy_ids=())


@pytest.mark.parametrize("raw,expected", [
    ("0,1,4,5,6,7,14,15", (0, 1, 4, 5, 6, 7, 14, 15)),
    ("0..3,5..7", (0, 1, 2, 3, 5, 6, 7)),
    ("12-15", (12, 13, 14, 15)),
    (" 3 , 3 ,1 ", (1, 3)),
    (None, ()),
])
def test_parse_allowed_phy_ids(raw, expected):
    assert abi.parse_allowed_phy_ids(raw) == expected


@pytest.mark.parametrize("raw", ["4..1", "x", "-1", "999999"])
def test_parse_allowed_phy_ids_rejects_malformed(raw):
    with pytest.raises(ProfilerUsageError):
        abi.parse_allowed_phy_ids(raw)


def test_vram_envelope_is_min_of_cap_and_free_minus_reserve():
    budget = abi.vram_budget(24 * abi.GIB, total_bytes=64 * abi.GIB)
    assert budget["cap_bytes"] == abi.S0_VRAM_CAP_BYTES
    assert budget["formula"] == "min(8 GiB, free_bytes - 2 GiB)"
    small = abi.vram_budget(6 * abi.GIB)
    assert small["cap_bytes"] == 4 * abi.GIB
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exhausted"):
        abi.vram_budget(abi.S0_VRAM_RESERVE_BYTES)
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_unknown"):
        abi.vram_budget(None)


def test_device_properties_report_missing_facts_instead_of_fabricating():
    properties = type("Props", (), {"name": "Ascend910B4", "total_memory": 64 * abi.GIB,
                                    "cube_core_num": 24})()
    npu = FakeNpu(properties=properties)
    facts = abi.device_properties(npu, 0)
    assert facts["aic_count"] == 24
    assert facts["hbm_bytes"] == 64 * abi.GIB
    assert facts["l2_bytes"] is None
    assert "l2_bytes" in facts["missing"]
    assert "vector_count" in facts["missing"]


def test_operator_registry_inspection_reports_schemas_and_missing_arguments():
    class Packet:
        def __init__(self, schema):
            self._schema = schema

        def overloads(self):
            return ["default"]

        @property
        def default(self):
            return self

    class Ops:
        npu = type("Npu", (), {
            "npu_grouped_matmul": Packet(
                "npu_grouped_matmul(Tensor[] x, Tensor[] w, int[] group_list, *, "
                "Tensor? per_token_scale=None, int group_list_type=0) -> Tensor[]"),
            "npu_fusion_attention": Packet(
                "npu_fusion_attention(Tensor q, Tensor k, Tensor v, int head_num, "
                "str input_layout) -> Tensor"),
        })()

    inspected = abi.inspect_operator_schemas({"npu": Ops.npu})
    by_key = {item["key"]: item for item in inspected["targets"]}
    grouped = by_key["npu_grouped_matmul"]
    assert grouped["available"] is True
    assert grouped["argument_support"] == {"per_token_scale": True,
                                          "group_list_type": True}
    assert grouped["missing_arguments"] == []
    assert by_key["npu_quant_matmul"]["available"] is False
    assert "npu_quant_matmul" in inspected["unavailable"]
    assert "npu_fusion_attention" in inspected["available"]


def test_numeric_canary_records_mismatch_and_unsupported_without_raising():
    assert abi.run_numeric_canary("ok", lambda: 2.0, lambda: 2.0)["status"] == "ok"
    assert abi.run_numeric_canary("off", lambda: 1.0, lambda: 5.0)["status"] == "mismatch"
    assert abi.run_numeric_canary("absent", None, 1.0)["status"] == "unavailable"

    def boom():
        raise RuntimeError("binding rejected")

    assert abi.run_numeric_canary("boom", boom, 1.0)["status"] == "unsupported_binding"


def test_portable_receipt_scrubs_home_address_device_and_digest(tmp_path):
    home = str(tmp_path / "home")
    payload = {
        "path": f"{home}/capture/rank_0",
        "host": "178.27.3.18",
        "device": "/dev/davinci7",
        "image": f"swr.example/a@sha256:{'a' * 64}",
        "nested": [{"note": "/root/secret"}],
        "count": 3,
    }
    scrubbed = abi.portable_receipt(payload, home=home)
    text = json.dumps(scrubbed)
    assert home not in text
    assert "178.27.3.18" not in text
    assert "/dev/davinci7" not in text
    assert "@sha256:" not in text
    assert scrubbed["count"] == 3
    assert abi.portable_violations(scrubbed, home=home) == []


def test_portable_violations_detects_each_forbidden_token():
    assert abi.portable_violations({"a": "/dev/davinci0"}) == ["device_node"]
    assert abi.portable_violations({"a": "10.1.2.3"}) == ["host_address"]
    assert abi.portable_violations({"a": f"x@sha256:{'b' * 64}"}) == ["image_digest"]
    assert abi.portable_violations({"a": "/home/someone/x"}) == ["home"]


@pytest.mark.parametrize("identifier,member", [
    ("bench-sku", "cases/1.json"),
    ("a1", "x"),
])
def test_capture_uri_is_relative_and_validated(identifier, member):
    assert abi.capture_uri(identifier, member) == f"capture://{identifier}/{member}"


@pytest.mark.parametrize("identifier,member", [
    ("Bad Id", "x"), ("ok", "/abs"), ("ok", "../escape"), ("ok", "a:b"),
    ("ok", "/home/user/x"), ("", "x"),
])
def test_capture_uri_rejects_unportable_members(identifier, member):
    with pytest.raises(ProfilerUsageError):
        abi.capture_uri(identifier, member)


def test_abi_receipt_is_portable_and_reports_no_prebind_probe(tmp_path):
    torch, npu = _torch()
    receipt = abi.build_abi_receipt(
        environ={abi.LOCAL_RANK_ENV: "1"}, torch=torch, torch_npu=npu,
        resolver=lambda ordinal: 13, namespaces={})
    assert receipt["schema"] == abi.ABI_SCHEMA
    assert receipt["device"]["ordinal"] == 1
    assert receipt["provenance"]["device_count_probed_before_bind"] is False
    assert receipt["provenance"]["source_uri"] == "capture://bench-abi/schema.json"
    assert abi.portable_violations(receipt) == []
    assert receipt["device_facts"]["budget"]["cap_bytes"] == abi.S0_VRAM_CAP_BYTES


def test_abi_cli_writes_atomic_json_for_a_fake_runtime(tmp_path, monkeypatch):
    torch, npu = _torch(free=3 * abi.GIB)
    monkeypatch.setattr(abi, "_load_torch", lambda: (torch, npu))
    monkeypatch.setenv(abi.LOCAL_RANK_ENV, "1")
    target = tmp_path / "abi.json"
    assert abi.main(["--out", str(target)]) == 0
    payload = json.loads(target.read_text())
    assert payload["status"] == "ok"
    assert payload["device"]["physical_id"] is None  # no installed resolver
    assert not list(Path(tmp_path).glob("*.tmp"))
    assert "device_count" not in npu.calls


def test_abi_cli_reports_binding_rejection_without_traceback(tmp_path, monkeypatch):
    torch, npu = _torch()
    monkeypatch.setattr(abi, "_load_torch", lambda: (torch, npu))
    monkeypatch.setenv(abi.LOCAL_RANK_ENV, "0")
    target = tmp_path / "rejected.json"
    code = abi.main(["--allowed-phy-ids", "12", "--out", str(target)])
    assert code == 2
    payload = json.loads(target.read_text())
    assert payload["status"] == "binding_rejected"
    assert "physical" in payload["reason"] or "unverifiable" in payload["reason"]


def test_visible_device_mask_reindexes_physical_ordinals():
    torch, npu = _torch()
    receipt = abi.bind_device(
        torch=torch, torch_npu=npu,
        environ={abi.LOCAL_RANK_ENV: "3",
                 abi.VISIBLE_DEVICES_ENV: "12,13,14,15"},
        allowed_phy_ids=(), resolver=lambda ordinal: 15)
    assert receipt["ordinal"] == 3
    assert receipt["visible_ordinal_count"] == 4
    with pytest.raises(ProfilerUsageError, match="bench_visible_device_mismatch"):
        abi.bind_device(
            torch=torch, torch_npu=npu,
            environ={abi.LOCAL_RANK_ENV: "12",
                     abi.VISIBLE_DEVICES_ENV: "12,13,14,15"},
            allowed_phy_ids=(), resolver=lambda ordinal: 12)
    sparse = abi.bind_device(
        torch=torch, torch_npu=npu,
        environ={abi.LOCAL_RANK_ENV: "12",
                 abi.VISIBLE_DEVICES_ENV: "12,13,14,15"},
        allowed_phy_ids=(), resolver=lambda ordinal: 12,
        sparse_visible_devices=True)
    assert sparse["ordinal"] == 12
    assert sparse["sparse_visible_devices"] is True


def test_memory_and_properties_prefer_the_torch_npu_surface():
    class Surface:
        def mem_get_info(self):
            return (7 * abi.GIB, 8 * abi.GIB)

        def get_device_properties(self, ordinal):
            return type("Props", (), {"name": "Ascend-from-torch",
                                      "cube_core_num": 20})()

    module_npu = type("ModuleNpu", (), {
        "mem_get_info": lambda self: (1, 2),
        "get_device_properties": lambda self, ordinal: None})()
    torch = type("Torch", (), {"npu": Surface()})()
    memory = abi.measure_memory(module_npu, 0, torch=torch)
    assert memory["free_bytes"] == 7 * abi.GIB
    facts = abi.device_properties(module_npu, 0, torch=torch)
    assert facts["aic_count"] == 20
    assert facts["source"] == "torch.npu.get_device_properties"


def test_portable_scrubbing_covers_ipv6_registries_and_encoded_paths():
    payload = {
        "ipv6": "2001:db8::1",
        "registry": "DOCKER.IO/team/image:tag",
        "swr": "SWR.CN-NORTH-1/team/image",
        "encoded": "%252Fhome%252Fsomeone%252Fcapture%252Frank0",
        "root": "/root",
        "volumes": "/" + "Volumes/external/capture",
        "mnt": "/mnt/scratch/capture",
        "home": "$" + "HOME/capture",
        "device": "/dev/davinci_manager",
        "digest": "sha256:" + "a" * 64 + "@sha" + "256:" + "b" * 64,
    }
    scrubbed = abi.portable_receipt(payload)
    text = json.dumps(scrubbed)
    for marker in ("2001:db8", "DOCKER.IO", "SWR.CN-", "%252F", "/root",
                   "/" + "Volumes/", "/mnt/", "$" + "HOME", "/dev/davinci", "@sha" + "256:"):
        assert marker not in text
    assert abi.portable_violations(scrubbed) == []
    assert abi.portable_violations({"ipv6": "2001:db8::1"}) == ["host_address"]
    assert "registry" in abi.portable_violations({"r": "docker.io/x"})


def test_operator_inspection_keeps_per_overload_arguments():
    class Packet:
        def __init__(self, schemas):
            self.schemas = schemas

        def overloads(self):
            return sorted(self.schemas)

        def __getattr__(self, name):
            if name in self.schemas:
                return type("Overload", (), {"_schema": self.schemas[name]})()
            raise AttributeError(name)

    packet = Packet({
        "int8": "op(Tensor x, Tensor w, *, Tensor? per_token_scale=None) -> Tensor",
        "fp8": "op(Tensor x, Tensor w, *, Tensor? scale=None) -> Tensor",
    })
    inspected = abi.inspect_operator_schemas({"npu": type("Ops", (), {
        "npu_quant_matmul": packet})()})
    grouped = inspected["targets"][0]
    by_overload = {item["overload"]: item["arguments"]
                   for item in grouped["overload_schemas"]}
    assert by_overload == {
        "fp8": ["scale", "w", "x"],
        "int8": ["per_token_scale", "w", "x"],
    }
    assert grouped["argument_support"]["per_token_scale"] is True
    assert grouped["arguments"] == ["per_token_scale", "scale", "w", "x"]
