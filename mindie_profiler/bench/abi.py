"""Device admission, operator-ABI inspection and portable receipts.

[Role]
  Bind the allocated NPU ordinal named by ``LOCAL_RANK`` before any other device
  query, verify the physical die id against a caller-supplied allowlist, enforce
  the S0 VRAM envelope, inspect installed operator schemas and device
  properties, run tiny numerical canaries, and emit only portable receipts.

[Invariants]
  * ``LOCAL_RANK`` is read first.  ``torch.npu.device_count()`` is never called
    before the bind: a shared host's device cgroup, not a count probe, protects
    the first bind.
  * ``ASCEND_RT_VISIBLE_DEVICES`` re-indexes the visible ordinals to
    ``0 .. len(mask) - 1``; a sparse physical-id launch requires explicit opt-in.
  * A caller-supplied physical allowlist fails closed.
  * Missing device facts stay ``None`` with an explicit ``missing`` entry;
    schema inspection uses explicit ``_schema`` / ``__text_signature__`` fields
    without ``inspect.signature``.
  * Receipts carry no ``$HOME``, host address, ``/dev/davinci*`` node or digest.

[Timeouts & Locks]
  Import is pure stdlib.  Device probes are single-shot; no locks or threads.

[Side-Effect Policy]
  Writes only the caller-requested ``--out`` JSON.
"""

from __future__ import annotations

import argparse, importlib, json, os, re, sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi_portable import (
    capture_uri,
    portable_receipt,
    portable_violations,
    scrub_portable,
    software_versions,
)
from .profiles import profile_section

ABI_SCHEMA = "mindie-bench-abi/1"
PHYSICAL_DIE_SCHEMA = "mindie-bench-physical-die/1"
LOCAL_RANK_ENV = "LOCAL_RANK"
WORLD_SIZE_ENV = "WORLD_SIZE"
ALLOWED_PHY_IDS_ENV = "MINDIE_BENCH_ALLOWED_PHY_IDS"
VISIBLE_DEVICES_ENV = "ASCEND_RT_VISIBLE_DEVICES"

_UNITS = profile_section("units")
_CFG = profile_section("abi")

KIB = int(_UNITS["kib"])
MIB = int(_UNITS["mib"])
GIB = int(_UNITS["gib"])
HZ_PER_MHZ = int(_UNITS["hz_per_mhz"])
MAX_DEVICE_ORDINAL = int(_CFG["max_device_ordinal"])
MAX_ALLOWED_PHY_IDS = int(_CFG["max_allowed_phy_ids"])
MAX_DIAGNOSTIC_CHARS = int(_CFG["max_diagnostic_chars"])
_MAX_OVERLOAD_SCHEMAS = int(_CFG["max_overload_schemas"])
S0_VRAM_CAP_BYTES = int(_CFG["s0_vram_cap_bytes"])
S0_VRAM_RESERVE_BYTES = int(_CFG["s0_vram_reserve_bytes"])
MAX_CLOCK_HZ = float(_CFG["max_clock_hz"])
_DECODE_DEPTH = int(_CFG["decode_depth"])
_IPV6_VERSION = int(_CFG["ipv6_version"])
_NAME_MAX_CHARS = int(_CFG["device_name_max_chars"])
_VER_MAX_CHARS = int(_CFG["version_max_chars"])
_DEFAULT_CANARY_TOL = float(_CFG["canary_default_tolerance"])
_EXIT_REJECTED = int(_CFG["exit_binding_rejected"])
_EXIT_UNAVAILABLE = int(_CFG["exit_torch_unavailable"])

CANN_OPS_NAMESPACE = "cann_ops_transformer"
NPU_OPS_NAMESPACE = "npu"

ABI_TARGETS: tuple[dict[str, Any], ...] = (
    {"key": "npu_quant_matmul", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ("per_token_scale",)},
    {"key": "npu_grouped_matmul", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ("per_token_scale", "group_list_type")},
    {"key": "npu_moe_init_routing_v2", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ()},
    {"key": "npu_fusion_attention", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ()},
    {"key": "npu_fused_infer_attention_score", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ()},
    {"key": "npu_incre_flash_attention", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"), "args": ()},
    {"key": "npu_chunk_gated_delta_rule", "namespaces": (NPU_OPS_NAMESPACE, "fla_npu"), "args": ()},
    {"key": "chunk_kda_fwd", "namespaces": ("fla_npu", "torch_npu"), "args": ()},
    {"key": "lightning_indexer", "namespaces": (CANN_OPS_NAMESPACE, "torch_npu"), "args": ()},
)

_PROPERTY_ALIASES = {
    "aic_count": ("cube_core_num", "aic_core_num", "aicore_num", "multi_processor_count"),
    "vector_count": ("vector_core_num", "aiv_core_num", "vector_num"),
    "clock_mhz": ("clock_rate_mhz", "clock_rate", "aic_clock_mhz"),
    "hbm_bytes": ("total_memory", "hbm_size", "memory_size"),
    "l2_bytes": ("l2_cache_size", "l2_bytes", "l2_cache_bytes"),
}

def _bounded_text(value: Any, limit: int = MAX_DIAGNOSTIC_CHARS) -> str:
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "..."


def resolve_local_rank(environ: Mapping[str, str] | None = None) -> int:
    """Read ``LOCAL_RANK`` before any device query; never probe a device count."""
    env = os.environ if environ is None else environ
    raw = env.get(LOCAL_RANK_ENV)
    if raw is None or not str(raw).strip():
        raise ProfilerUsageError(
            "bench_device_rank_missing: LOCAL_RANK must be exported by the launcher "
            "before binding; the bench never probes torch.npu.device_count() first"
        )
    try:
        ordinal = int(str(raw).strip())
    except ValueError as exc:
        raise ProfilerUsageError(
            f"bench_device_rank_invalid: LOCAL_RANK={_bounded_text(raw)!r}"
        ) from exc
    if ordinal < 0 or ordinal > MAX_DEVICE_ORDINAL:
        raise ProfilerUsageError(
            f"bench_device_rank_invalid: LOCAL_RANK={ordinal} outside "
            f"[0, {MAX_DEVICE_ORDINAL}]"
        )
    return ordinal


def parse_device_mask(raw: Any) -> tuple[int, ...]:
    """Parse ``ASCEND_RT_VISIBLE_DEVICES``-style comma/range ordinals."""
    if raw is None:
        return ()
    text = str(raw).strip()
    if not text:
        return ()
    values: set[int] = set()
    for token in re.split(r"[,;]", text):
        token = token.strip()
        if not token:
            continue
        bounds = re.split(r"\.\.|-|:", token)
        if len(bounds) == 1:
            bounds = [bounds[0], bounds[0]]
        if len(bounds) != 2:
            raise ProfilerUsageError(f"bench_device_mask_invalid: {_bounded_text(token)!r}")
        try:
            low, high = int(bounds[0]), int(bounds[1])
        except ValueError as exc:
            raise ProfilerUsageError(
                f"bench_device_mask_invalid: {_bounded_text(token)!r}"
            ) from exc
        if low > high or low < 0 or high > MAX_DEVICE_ORDINAL:
            raise ProfilerUsageError(f"bench_device_mask_invalid: {_bounded_text(token)!r}")
        values.update(range(low, high + 1))
        if len(values) > MAX_ALLOWED_PHY_IDS:
            raise ProfilerUsageError("bench_device_mask_invalid: too many ordinals")
    return tuple(sorted(values))


def parse_allowed_phy_ids(raw: Any) -> tuple[int, ...]:
    """Parse the caller-supplied physical die allowlist (fail-closed guard)."""
    return parse_device_mask(raw)


def resolve_allowed_phy_ids(
    cli_value: Any = None, environ: Mapping[str, str] | None = None
) -> tuple[int, ...]:
    """Prefer the explicit ``--allowed-phy-ids`` flag over the environment."""
    if cli_value is not None:
        return parse_allowed_phy_ids(cli_value)
    env = os.environ if environ is None else environ
    return parse_allowed_phy_ids(env.get(ALLOWED_PHY_IDS_ENV))


def _platform_resolver() -> Any:
    try:
        module = importlib.import_module("vllm_ascend.platform")
    except TimeoutError:
        raise
    except Exception:
        return None
    platform_cls = getattr(module, "NPUPlatform", None)
    resolver = getattr(platform_cls, "visible_device_id_to_physical_device_id", None)
    return resolver if callable(resolver) else None


def _property_value(properties: Any, aliases: Sequence[str]) -> Any:
    mapping = properties if isinstance(properties, Mapping) else None
    for name in aliases:
        value = (
            mapping.get(name) if mapping is not None else getattr(properties, name, None)
        )
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if value > 0:
            return value
    return None


def _npu_surface(torch_npu: Any, torch: Any = None, method: str = "") -> Any:
    surface = getattr(torch, "npu", None) if torch is not None else None
    if surface is not None and callable(getattr(surface, method, None)):
        return surface
    return torch_npu


def device_properties(
    torch_npu: Any, ordinal: int, *, torch: Any = None
) -> dict[str, Any]:
    """Read the installed device facts; absent values stay ``None``."""
    facts: dict[str, Any] = {key: None for key in _PROPERTY_ALIASES}
    facts["name"] = None
    surface = _npu_surface(torch_npu, torch, "get_device_properties")
    try:
        getter = getattr(surface, "get_device_properties", None)
        properties = getter(ordinal) if callable(getter) else None
    except TimeoutError:
        raise
    except Exception as exc:
        properties = None
        facts["missing"] = [f"device_properties:{_bounded_text(exc)}"]
    facts["name"] = _bounded_text(getattr(properties, "name", "") or "", _NAME_MAX_CHARS) or None
    for key, aliases in _PROPERTY_ALIASES.items():
        value = _property_value(properties, aliases)
        if key == "clock_mhz" and isinstance(value, float) and value > MAX_CLOCK_HZ:
            value = value / HZ_PER_MHZ
        facts[key] = value
    missing = [key for key in _PROPERTY_ALIASES if facts.get(key) is None]
    facts["missing"] = sorted(set(facts.get("missing", [])) | set(missing))
    facts["source"] = (
        "torch.npu.get_device_properties"
        if surface is not torch_npu
        else "torch_npu.get_device_properties"
    )
    return facts


def resolve_physical_die(ordinal: int, *, resolver: Any = None) -> dict[str, Any]:
    """Resolve the physical die id of an already bound ordinal."""
    source, physical = "unavailable", None
    candidate = resolver if callable(resolver) else _platform_resolver()
    if callable(candidate):
        source = "vllm_ascend.NPUPlatform.visible_device_id_to_physical_device_id"
        try:
            resolved = candidate(ordinal)
        except TimeoutError:
            raise
        except Exception as exc:
            return {
                "schema": PHYSICAL_DIE_SCHEMA,
                "ordinal": int(ordinal),
                "physical_id": None,
                "source": source,
                "error": _bounded_text(exc),
            }
        if isinstance(resolved, int) and not isinstance(resolved, bool):
            physical = resolved
        elif isinstance(resolved, (list, tuple)) and len(resolved) == 1:
            physical = int(resolved[0])
    return {
        "schema": PHYSICAL_DIE_SCHEMA,
        "ordinal": int(ordinal),
        "physical_id": physical,
        "source": source,
        "error": None,
    }


def bind_device(
    *,
    torch: Any = None,
    torch_npu: Any = None,
    environ: Mapping[str, str] | None = None,
    allowed_phy_ids: Iterable[int] = (),
    resolver: Any = None,
    sparse_visible_devices: bool = False,
    sparse_unmasked: bool = False,
    visible_device_map: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Bind ``LOCAL_RANK`` then verify the physical die id (fail-closed)."""
    env = os.environ if environ is None else environ
    ordinal = resolve_local_rank(env)
    mask = parse_device_mask(env.get(VISIBLE_DEVICES_ENV))
    sparse_allowed = bool(
        sparse_visible_devices or sparse_unmasked or visible_device_map is not None
    )
    if mask:
        sparse_member = sparse_allowed and ordinal in mask
        if ordinal >= len(mask) and not sparse_member:
            raise ProfilerUsageError(
                f"bench_visible_device_mismatch: LOCAL_RANK={ordinal} must be in "
                f"[0, {len(mask) - 1}] for {VISIBLE_DEVICES_ENV}={list(mask)} "
                "because CANN exposes one visible ordinal per mask entry"
            )
    allowed = tuple(sorted(int(item) for item in (allowed_phy_ids or ())))
    if torch is None or torch_npu is None:
        raise ProfilerUsageError("bench_device_binding_requires_torch_npu")
    setter = getattr(getattr(torch, "npu", None), "set_device", None)
    if not callable(setter):
        raise ProfilerUsageError("bench_device_binding_requires_torch_npu")
    setter(ordinal)
    die = resolve_physical_die(ordinal, resolver=resolver)
    physical = die.get("physical_id")
    if allowed:
        if physical is None:
            raise ProfilerUsageError(
                "bench_physical_die_unverifiable: an allowlist was supplied but the "
                "post-bind physical die id could not be resolved"
            )
        if physical not in allowed:
            raise ProfilerUsageError(
                f"bench_physical_die_not_allowed: ordinal {ordinal} maps to physical "
                f"die {physical}, allowed {list(allowed)}"
            )
    return {
        "schema": PHYSICAL_DIE_SCHEMA,
        "ordinal": ordinal,
        "visible_devices": list(mask) if mask else None,
        "visible_ordinal_count": len(mask) if mask else None,
        "sparse_visible_devices": bool(sparse_visible_devices),
        "physical_id": physical,
        "physical_source": die.get("source"),
        "physical_error": die.get("error"),
        "allowed_phy_ids": list(allowed) if allowed else None,
        "allowed": (bool(physical in allowed) if allowed and physical is not None else None),
        "verified": bool(physical is not None),
    }


def vram_budget(free_bytes: Any, *, total_bytes: Any = None) -> dict[str, Any]:
    """S0 envelope: ``min(8 GiB, free - 2 GiB)``; never a negative cap."""
    free = _positive_or_none(free_bytes)
    total = _positive_or_none(total_bytes)
    if free is None:
        raise ProfilerUsageError(
            "bench_vram_budget_unknown: free device memory must be measured before "
            "the S0 envelope is used"
        )
    if free <= S0_VRAM_RESERVE_BYTES:
        raise ProfilerUsageError(
            f"bench_vram_budget_exhausted: free_bytes={free} does not exceed the "
            f"{S0_VRAM_RESERVE_BYTES}-byte reserve"
        )
    cap = min(S0_VRAM_CAP_BYTES, free - S0_VRAM_RESERVE_BYTES)
    return {
        "schema": "mindie-bench-vram-budget/1",
        "cap_bytes": cap,
        "free_bytes": free,
        "total_bytes": total,
        "reserve_bytes": S0_VRAM_RESERVE_BYTES,
        "cap_limit_bytes": S0_VRAM_CAP_BYTES,
        "formula": "min(8 GiB, free_bytes - 2 GiB)",
        "measured": True,
    }


def _positive_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return int(value)


def _read_memory(getter: Any, ordinal: int | None) -> Any:
    if ordinal is None:
        return getter()
    try:
        return getter()
    except TypeError:
        return getter(int(ordinal))


def measure_memory(
    torch_npu: Any, ordinal: int | None = None, *, torch: Any = None
) -> dict[str, Any]:
    """Read free/total device memory from ``torch.npu.mem_get_info``."""
    surface = _npu_surface(torch_npu, torch, "mem_get_info")
    getter = getattr(surface, "mem_get_info", None)
    if not callable(getter):
        return {
            "measured": False,
            "free_bytes": None,
            "total_bytes": None,
            "missing": ["mem_get_info"],
        }
    try:
        payload = _read_memory(getter, ordinal)
    except TimeoutError:
        raise
    except Exception as exc:
        return {
            "measured": False,
            "free_bytes": None,
            "total_bytes": None,
            "missing": [_bounded_text(exc)],
        }
    if isinstance(payload, (list, tuple)) and len(payload) >= 2:
        free, total = payload[0], payload[1]
    elif isinstance(payload, Mapping):
        free, total = payload.get("free"), payload.get("total")
    else:
        free = total = None
    return {
        "measured": _positive_or_none(free) is not None,
        "free_bytes": _positive_or_none(free),
        "total_bytes": _positive_or_none(total),
        "missing": [],
    }


def _namespace_object(namespaces: Mapping[str, Any], name: str) -> Any:
    if name in namespaces:
        return namespaces[name]
    try:
        return importlib.import_module(name)
    except TimeoutError:
        raise
    except Exception:
        return None


def _schema_arguments(schema: Any) -> tuple[str, ...]:
    text = str(schema or "")
    start, end = text.find("("), text.find(")", text.find("(") + 1)
    if start < 0 or end < 0:
        return ()
    names: list[str] = []
    for part in re.split(r",(?![^()]*\))", text[start + 1 : end]):
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", part.split("=", 1)[0].strip())
        if identifiers:
            names.append(identifiers[-1])
    return tuple(names)


def inspect_operator_schemas(namespaces: Mapping[str, Any]) -> dict[str, Any]:
    """Enumerate installed operator packets, overloads and schemas without inspect.signature."""
    entries: list[dict[str, Any]] = []
    for target in ABI_TARGETS:
        record: dict[str, Any] = {
            "key": target["key"],
            "available": False,
            "namespace": None,
            "overloads": [],
            "schemas": [],
            "overload_schemas": [],
            "python_signature": None,
            "arguments": [],
            "required_arguments": list(target["args"]),
            "argument_support": {name: False for name in target["args"]},
            "missing_arguments": list(target["args"]),
        }
        for namespace in target["namespaces"]:
            container = _namespace_object(namespaces, namespace)
            packet = getattr(container, target["key"], None) if container is not None else None
            if packet is None:
                continue
            record.update({"available": True, "namespace": namespace})
            overloads = getattr(packet, "overloads", None)
            names = list(overloads()) if callable(overloads) else []
            record["overloads"] = [str(name) for name in names]
            arguments: list[str] = []
            for name in names:
                try:
                    schema = getattr(packet, str(name))._schema
                except TimeoutError:
                    raise
                except Exception:
                    continue
                overload_arguments = _schema_arguments(schema)
                arguments.extend(overload_arguments)
                if len(record["schemas"]) < _MAX_OVERLOAD_SCHEMAS:
                    record["schemas"].append(_bounded_text(schema))
                if len(record["overload_schemas"]) < _MAX_OVERLOAD_SCHEMAS:
                    record["overload_schemas"].append(
                        {
                            "overload": str(name),
                            "schema": _bounded_text(schema),
                            "arguments": sorted(set(overload_arguments)),
                        }
                    )
            if not names:
                schema = getattr(packet, "_schema", None)
                if schema is not None:
                    record["schemas"].append(_bounded_text(schema))
                    overload_arguments = _schema_arguments(schema)
                    arguments.extend(overload_arguments)
                    record["overload_schemas"].append(
                        {
                            "overload": "default",
                            "schema": _bounded_text(schema),
                            "arguments": sorted(set(overload_arguments)),
                        }
                    )
            text_sig = getattr(packet, "__text_signature__", None)
            code_obj = getattr(packet, "__code__", None)
            if text_sig:
                record["python_signature"] = _bounded_text(text_sig)
                arguments.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(text_sig)))
            elif code_obj is not None:
                varnames = tuple(getattr(code_obj, "co_varnames", ()))
                arg_total = int(getattr(code_obj, "co_argcount", 0)) + int(
                    getattr(code_obj, "co_kwonlyargcount", 0)
                )
                arguments.extend(varnames[:arg_total])
            supported = set(arguments)
            record["arguments"] = sorted(supported)
            record["argument_support"] = {
                name: name in supported for name in target["args"]
            }
            record["missing_arguments"] = [
                name for name in target["args"] if name not in supported
            ]
            break
        entries.append(record)
    return {
        "targets": entries,
        "available": sorted(item["key"] for item in entries if item["available"]),
        "unavailable": sorted(item["key"] for item in entries if not item["available"]),
    }


def _numeric_equal(actual: Any, expected: Any, tolerance: float) -> bool:
    try:
        difference = abs(float(actual) - float(expected))
    except (TypeError, ValueError):
        return False
    scale = max(1.0, abs(float(expected)))
    return difference <= tolerance * scale


def run_numeric_canary(
    name: str,
    callable_: Any,
    reference: Any,
    *,
    tolerance: float = _DEFAULT_CANARY_TOL,
) -> dict[str, Any]:
    """Run one tiny numerical canary; never promotes a failure into a crash."""
    if not callable(callable_):
        return {"name": name, "status": "unavailable", "reason": "callable_absent"}
    try:
        produced = callable_()
        expected = reference() if callable(reference) else reference
        produced_value = produced.item() if hasattr(produced, "item") else produced
    except TimeoutError:
        raise
    except Exception as exc:
        return {"name": name, "status": "unsupported_binding", "reason": _bounded_text(exc)}
    matched = _numeric_equal(produced_value, expected, tolerance)
    return {
        "name": name,
        "status": "ok" if matched else "mismatch",
        "actual": produced_value,
        "expected": expected,
        "tolerance": tolerance,
    }


def _device_receipt(
    torch_npu: Any, ordinal: int, *, torch: Any = None
) -> dict[str, Any]:
    properties = device_properties(torch_npu, ordinal, torch=torch)
    memory = measure_memory(torch_npu, ordinal, torch=torch)
    receipt: dict[str, Any] = {"ordinal": ordinal, "properties": properties, "memory": memory}
    try:
        receipt["budget"] = vram_budget(
            memory.get("free_bytes"), total_bytes=memory.get("total_bytes")
        )
    except ProfilerUsageError as exc:
        receipt["budget"] = None
        receipt["budget_refusal"] = _bounded_text(exc)
    return receipt


def _load_torch() -> tuple[Any, Any]:
    torch = importlib.import_module("torch")
    torch_npu = importlib.import_module("torch_npu")
    importlib.import_module("torch.distributed")
    return torch, torch_npu


def _abi_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench abi",
        description=(
            "Bind LOCAL_RANK, verify the physical die, inspect operator ABIs "
            "and device properties, run numerical canaries."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--allowed-phy-ids",
        default=None,
        help="physical die allowlist, e.g. '12..15' or '0,1,4,5'",
    )
    parser.add_argument(
        "--sparse-visible-devices",
        action="store_true",
        help="LOCAL_RANK carries a physical id from a sparse ASCEND_RT_VISIBLE_DEVICES map",
    )
    parser.add_argument(
        "--export-builders",
        action="store_true",
        help="pure-CPU export of the canonical CANN + non-CANN BuilderSpec catalog",
    )
    parser.add_argument(
        "--out",
        "--output",
        dest="output",
        default=None,
        help="write JSON here (atomic); otherwise print to stdout",
    )
    return parser


def build_abi_receipt(
    *,
    allowed_phy_ids: Sequence[int] = (),
    environ: Mapping[str, str] | None = None,
    torch: Any = None,
    torch_npu: Any = None,
    resolver: Any = None,
    sparse_visible_devices: bool = False,
    namespaces: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the abi receipt from an explicit device/torch context."""
    torch = torch if torch is not None else _load_torch()[0]
    torch_npu = torch_npu if torch_npu is not None else _load_torch()[1]
    binding = bind_device(
        torch=torch,
        torch_npu=torch_npu,
        environ=environ,
        allowed_phy_ids=allowed_phy_ids,
        resolver=resolver,
        sparse_visible_devices=sparse_visible_devices,
    )
    modules: dict[str, Any] = {"torch": torch, "torch_npu": torch_npu}
    for label in ("vllm_ascend", "fla_npu", "flash_attn_npu"):
        try:
            modules[label] = importlib.import_module(label)
        except TimeoutError:
            raise
        except Exception:
            modules[label] = None
    if namespaces is None:
        namespaces = {}
        ops = getattr(torch, "ops", None)
        for name in (NPU_OPS_NAMESPACE, CANN_OPS_NAMESPACE):
            container = getattr(ops, name, None) if ops is not None else None
            if container is not None:
                namespaces[name] = container
    operators = inspect_operator_schemas(namespaces)
    device = _device_receipt(torch_npu, binding["ordinal"], torch=torch)
    receipt = {
        "schema": ABI_SCHEMA,
        "status": "ok",
        "device": binding,
        "device_facts": device,
        "operators": operators,
        "canaries": _canaries(torch, namespaces, binding["ordinal"]),
        "software": software_versions(modules),
        "provenance": {
            "source_uri": capture_uri("bench-abi", "schema.json"),
            "probe": "installed_operator_registry",
            "device_count_probed_before_bind": False,
        },
    }
    return portable_receipt(receipt, home=os.environ.get("HOME"))


def _canaries(
    torch: Any, namespaces: Mapping[str, Any], ordinal: int = 0
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    add = getattr(torch, "add", None)
    ones = getattr(torch, "ones", None)
    npu = getattr(torch, "npu", None)
    if callable(add) and callable(ones):
        device = f"npu:{int(ordinal)}"
        kwargs = {"device": device} if npu is not None else {}

        def run_vector_add() -> Any:
            dtype = getattr(torch, "float32", None)
            left = ones(1, dtype=dtype, **kwargs)
            return add(left, left).item()

        results.append(run_numeric_canary("vector_add_unit", run_vector_add, lambda: 2.0))
    for target in ABI_TARGETS:
        container = next(
            (namespaces[name] for name in target["namespaces"] if name in namespaces),
            None,
        )
        packet = getattr(container, target["key"], None) if container is not None else None
        if packet is None:
            results.append(
                {
                    "name": f"schema:{target['key']}",
                    "status": "unavailable",
                    "reason": "operator_absent",
                }
            )
            continue
        overloads = getattr(packet, "overloads", None)
        names = list(overloads()) if callable(overloads) else []
        results.append(
            {"name": f"schema:{target['key']}", "status": "ok", "overload_count": len(names)}
        )
    return results


def main(argv: Sequence[str] | None = None) -> int:
    args = _abi_parser().parse_args(list(argv or ()))
    if args.export_builders:
        from .operators import export_builder_catalog

        _emit(portable_receipt(export_builder_catalog(), home=os.environ.get("HOME")), args.output)
        return 0
    allowed = parse_allowed_phy_ids(
        args.allowed_phy_ids
        if args.allowed_phy_ids is not None
        else os.environ.get(ALLOWED_PHY_IDS_ENV)
    )
    try:
        torch, torch_npu = _load_torch()
    except TimeoutError:
        raise
    except Exception as exc:
        _emit(
            {"schema": ABI_SCHEMA, "status": "torch_npu_unavailable", "reason": _bounded_text(exc)},
            args.output,
        )
        return _EXIT_UNAVAILABLE
    try:
        receipt = build_abi_receipt(
            allowed_phy_ids=allowed,
            torch=torch,
            torch_npu=torch_npu,
            sparse_visible_devices=bool(args.sparse_visible_devices),
        )
    except ProfilerUsageError as exc:
        payload = portable_receipt(
            {"schema": ABI_SCHEMA, "status": "binding_rejected", "reason": _bounded_text(exc)},
            home=os.environ.get("HOME"),
        )
        _emit(payload, args.output)
        return _EXIT_REJECTED
    _emit(receipt, args.output)
    return 0


def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")}, sort_keys=True))
        return
    sys.stdout.write(text)


__all__ = [
    "ABI_SCHEMA", "ABI_TARGETS", "ALLOWED_PHY_IDS_ENV", "LOCAL_RANK_ENV",
    "MAX_DEVICE_ORDINAL", "PHYSICAL_DIE_SCHEMA", "S0_VRAM_CAP_BYTES",
    "S0_VRAM_RESERVE_BYTES", "VISIBLE_DEVICES_ENV", "bind_device",
    "build_abi_receipt", "capture_uri", "device_properties",
    "inspect_operator_schemas", "main", "measure_memory", "parse_allowed_phy_ids",
    "parse_device_mask", "portable_receipt", "portable_violations",
    "resolve_allowed_phy_ids", "resolve_local_rank", "resolve_physical_die",
    "run_numeric_canary", "scrub_portable", "software_versions", "vram_budget",
]

if __name__ == "__main__":
    raise SystemExit(main())
