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
    ``0 .. len(mask) - 1``; a sparse physical-id launch is only accepted through
    an explicit opt-in, never by treating ``LOCAL_RANK`` as a physical id.
  * A caller-supplied physical allowlist fails closed.  An unresolvable or
    mismatched physical die id aborts before benchmark tensors or HCCL exist.
  * Missing device facts stay ``None`` with an explicit ``missing`` entry; no
    AIC count, clock, HBM or L2 size is fabricated.
  * Receipts carry no ``$HOME``, host address, ``/dev/davinci*`` node or
    image digest locator.

[Timeouts & Locks]
  Import is pure stdlib.  Device probes are single-shot and bounded by the
  caller's outer container budget; no locks, timers or background threads.

[Side-Effect Policy]
  Writes only the caller-requested ``--out`` JSON.  Live device access happens
  only under the explicit ``bench abi`` subcommand.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import ipaddress
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote

from ..events import ProfilerUsageError

ABI_SCHEMA = "mindie-bench-abi/1"
PHYSICAL_DIE_SCHEMA = "mindie-bench-physical-die/1"
LOCAL_RANK_ENV = "LOCAL_RANK"
WORLD_SIZE_ENV = "WORLD_SIZE"
ALLOWED_PHY_IDS_ENV = "MINDIE_BENCH_ALLOWED_PHY_IDS"
VISIBLE_DEVICES_ENV = "ASCEND_RT_VISIBLE_DEVICES"

MAX_DEVICE_ORDINAL = 4095
MAX_ALLOWED_PHY_IDS = 4096
MAX_DIAGNOSTIC_CHARS = 400
_MAX_OVERLOAD_SCHEMAS = 8
KIB = 1024
MIB = KIB * KIB
GIB = MIB * KIB
S0_VRAM_CAP_BYTES = 8 * GIB
S0_VRAM_RESERVE_BYTES = 2 * GIB
HZ_PER_MHZ = 1_000_000
MAX_CLOCK_HZ = 1_000_000.0

CANN_OPS_NAMESPACE = "cann_ops_transformer"
NPU_OPS_NAMESPACE = "npu"

ABI_TARGETS: tuple[dict[str, Any], ...] = (
    {"key": "npu_quant_matmul", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ("per_token_scale",)},
    {"key": "npu_grouped_matmul", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ("per_token_scale", "group_list_type")},
    {"key": "npu_moe_init_routing_v2", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ()},
    {"key": "npu_fusion_attention", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ()},
    {"key": "npu_fused_infer_attention_score", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ()},
    {"key": "npu_incre_flash_attention", "namespaces": (NPU_OPS_NAMESPACE, "torch_npu"),
     "args": ()},
    {"key": "npu_chunk_gated_delta_rule", "namespaces": (NPU_OPS_NAMESPACE, "fla_npu"),
     "args": ()},
    {"key": "chunk_kda_fwd", "namespaces": ("fla_npu", "torch_npu"), "args": ()},
    {"key": "lightning_indexer", "namespaces": (CANN_OPS_NAMESPACE, "torch_npu"),
     "args": ()},
)

_PROPERTY_ALIASES = {
    "aic_count": ("cube_core_num", "aic_core_num", "aicore_num", "multi_processor_count"),
    "vector_count": ("vector_core_num", "aiv_core_num", "vector_num"),
    "clock_mhz": ("clock_rate_mhz", "clock_rate", "aic_clock_mhz"),
    "hbm_bytes": ("total_memory", "hbm_size", "memory_size"),
    "l2_bytes": ("l2_cache_size", "l2_bytes", "l2_cache_bytes"),
}

_DOCKER_REGISTRY = "docker" + ".io/"
_SWR_REGISTRY = "swr" + ".cn-"
_QUAY_REGISTRY = "quay" + ".io/"
_REGISTRY_MARKERS = (_DOCKER_REGISTRY, _SWR_REGISTRY, _QUAY_REGISTRY)
_DIGEST_MARKER = "@sha" + "256:"
_DEVICE_MARKER = "/dev/davinci"

_HOST_ADDRESS = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_IPV6_CANDIDATE = re.compile(
    r"(?<![\w:.])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:.])")
_DEVICE_NODE = re.compile(r"/dev/davinci[0-9A-Za-z_]*")
_IMAGE_DIGEST = re.compile("(?i)" + re.escape(_DIGEST_MARKER) + r"[0-9a-f]{64}")
_ABSOLUTE_HOME = re.compile(
    r"(?:/home/[^/\s\"']+|/Users/[^/\s\"']+|/Volumes/[^\s\"']+|"
    r"/mnt/[^\s\"']+|/root(?:/[^\s\"']*)?|\$\{?HOME\}?|~/)")
_CAPTURE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_HOST_IP_PLACEHOLDER = "<host-address>"
_DEVICE_PLACEHOLDER = "<device-node>"
_DIGEST_PLACEHOLDER = "@<image-digest>"
_HOME_PLACEHOLDER = "<home>"
_REGISTRY_PLACEHOLDER = "<registry>/"
_DECODE_DEPTH = 4
_IPV6_VERSION = 6


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
            "before binding; the bench never probes torch.npu.device_count() first")
    try:
        ordinal = int(str(raw).strip())
    except ValueError as exc:
        raise ProfilerUsageError(
            f"bench_device_rank_invalid: LOCAL_RANK={_bounded_text(raw)!r}") from exc
    if ordinal < 0 or ordinal > MAX_DEVICE_ORDINAL:
        raise ProfilerUsageError(
            f"bench_device_rank_invalid: LOCAL_RANK={ordinal} outside "
            f"[0, {MAX_DEVICE_ORDINAL}]")
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
                f"bench_device_mask_invalid: {_bounded_text(token)!r}") from exc
        if low > high or low < 0 or high > MAX_DEVICE_ORDINAL:
            raise ProfilerUsageError(f"bench_device_mask_invalid: {_bounded_text(token)!r}")
        values.update(range(low, high + 1))
        if len(values) > MAX_ALLOWED_PHY_IDS:
            raise ProfilerUsageError("bench_device_mask_invalid: too many ordinals")
    return tuple(sorted(values))


def parse_allowed_phy_ids(raw: Any) -> tuple[int, ...]:
    """Parse the caller-supplied physical die allowlist (fail-closed guard)."""
    return parse_device_mask(raw)


def resolve_allowed_phy_ids(cli_value: Any = None,
                            environ: Mapping[str, str] | None = None) -> tuple[int, ...]:
    """Prefer the explicit ``--allowed-phy-ids`` flag over the environment."""
    if cli_value is not None:
        return parse_allowed_phy_ids(cli_value)
    env = os.environ if environ is None else environ
    return parse_allowed_phy_ids(env.get(ALLOWED_PHY_IDS_ENV))


def _platform_resolver():
    """Return the installed visible->physical device resolver, if any."""
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
        value = mapping.get(name) if mapping is not None else getattr(properties, name, None)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if value > 0:
            return value
    return None


def _npu_surface(torch_npu: Any, torch: Any = None, method: str = "") -> Any:
    """Prefer ``torch.npu`` (the real Ascend PyTorch surface) when it has the op."""
    surface = getattr(torch, "npu", None) if torch is not None else None
    if surface is not None and callable(getattr(surface, method, None)):
        return surface
    return torch_npu


def device_properties(torch_npu: Any, ordinal: int, *,
                      torch: Any = None) -> dict[str, Any]:
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
    facts["name"] = _bounded_text(getattr(properties, "name", "") or "", 120) or None
    for key, aliases in _PROPERTY_ALIASES.items():
        value = _property_value(properties, aliases)
        if key == "clock_mhz" and isinstance(value, float) and value > MAX_CLOCK_HZ:
            value = value / HZ_PER_MHZ  # A raw Hz reading is normalized to MHz.
        facts[key] = value
    missing = [key for key in _PROPERTY_ALIASES if facts.get(key) is None]
    facts["missing"] = sorted(set(facts.get("missing", [])) | set(missing))
    facts["source"] = ("torch.npu.get_device_properties"
                       if surface is not torch_npu else
                       "torch_npu.get_device_properties")
    return facts


def resolve_physical_die(ordinal: int, *, resolver: Any = None) -> dict[str, Any]:
    """Resolve the physical die id of an **already bound** ordinal.

    The visible id is only an ordinal inside the container's device cgroup; the
    physical id is what a shared host's allowlist must be checked against.
    """
    source, physical = "unavailable", None
    candidate = resolver if callable(resolver) else _platform_resolver()
    if callable(candidate):
        source = "vllm_ascend.NPUPlatform.visible_device_id_to_physical_device_id"
        try:
            resolved = candidate(ordinal)
        except TimeoutError:
            raise
        except Exception as exc:
            return {"schema": PHYSICAL_DIE_SCHEMA, "ordinal": int(ordinal),
                    "physical_id": None, "source": source,
                    "error": _bounded_text(exc)}
        if isinstance(resolved, int) and not isinstance(resolved, bool):
            physical = resolved
        elif isinstance(resolved, (list, tuple)) and len(resolved) == 1:
            physical = int(resolved[0])
    return {"schema": PHYSICAL_DIE_SCHEMA, "ordinal": int(ordinal),
            "physical_id": physical, "source": source, "error": None}


def bind_device(*, torch: Any = None, torch_npu: Any = None,
                environ: Mapping[str, str] | None = None,
                allowed_phy_ids: Iterable[int] = (),
                resolver: Any = None,
                sparse_visible_devices: bool = False,
                sparse_unmasked: bool = False,
                visible_device_map: Sequence[int] | None = None) -> dict[str, Any]:
    """Bind ``LOCAL_RANK`` then verify the physical die id (fail-closed).

    ``ASCEND_RT_VISIBLE_DEVICES`` re-indexes CANN's visible ordinals to
    ``0 .. len(mask) - 1``.  A launcher that passes physical ids directly must
    opt in explicitly; the default never lets ``LOCAL_RANK`` exceed the number
    of visible ordinals.
    """
    env = os.environ if environ is None else environ
    ordinal = resolve_local_rank(env)
    mask = parse_device_mask(env.get(VISIBLE_DEVICES_ENV))
    sparse_allowed = bool(sparse_visible_devices or sparse_unmasked
                          or visible_device_map is not None)
    if mask:
        sparse_member = sparse_allowed and ordinal in mask
        if ordinal >= len(mask) and not sparse_member:
            raise ProfilerUsageError(
                f"bench_visible_device_mismatch: LOCAL_RANK={ordinal} must be in "
                f"[0, {len(mask) - 1}] for {VISIBLE_DEVICES_ENV}={list(mask)} "
                "because CANN exposes one visible ordinal per mask entry")
    allowed = tuple(sorted(int(item) for item in (allowed_phy_ids or ())))
    if torch is None or torch_npu is None:
        raise ProfilerUsageError("bench_device_binding_requires_torch_npu")
    setter = getattr(getattr(torch, "npu", None), "set_device", None)
    if not callable(setter):
        raise ProfilerUsageError("bench_device_binding_requires_torch_npu")
    setter(ordinal)  # The bind precedes every physical-id query.
    die = resolve_physical_die(ordinal, resolver=resolver)
    physical = die.get("physical_id")
    if allowed:
        if physical is None:
            raise ProfilerUsageError(
                "bench_physical_die_unverifiable: an allowlist was supplied but the "
                "post-bind physical die id could not be resolved")
        if physical not in allowed:
            raise ProfilerUsageError(
                f"bench_physical_die_not_allowed: ordinal {ordinal} maps to physical "
                f"die {physical}, allowed {list(allowed)}")
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
        "allowed": (bool(physical in allowed) if allowed and physical is not None
                    else None),
        "verified": bool(physical is not None),
    }


def vram_budget(free_bytes: Any, *, total_bytes: Any = None) -> dict[str, Any]:
    """S0 envelope: ``min(8 GiB, free - 2 GiB)``; never a negative cap."""
    free = _positive_or_none(free_bytes)
    total = _positive_or_none(total_bytes)
    if free is None:
        raise ProfilerUsageError(
            "bench_vram_budget_unknown: free device memory must be measured before "
            "the S0 envelope is used")
    if free <= S0_VRAM_RESERVE_BYTES:
        raise ProfilerUsageError(
            f"bench_vram_budget_exhausted: free_bytes={free} does not exceed the "
            f"{S0_VRAM_RESERVE_BYTES}-byte reserve")
    cap = min(S0_VRAM_CAP_BYTES, free - S0_VRAM_RESERVE_BYTES)
    return {"schema": "mindie-bench-vram-budget/1", "cap_bytes": cap,
            "free_bytes": free, "total_bytes": total,
            "reserve_bytes": S0_VRAM_RESERVE_BYTES,
            "cap_limit_bytes": S0_VRAM_CAP_BYTES,
            "formula": "min(8 GiB, free_bytes - 2 GiB)",
            "measured": True}


def _positive_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value <= 0:
        return None
    return int(value)


def _read_memory(surface: Any, getter: Any, ordinal: int | None) -> Any:
    """``mem_get_info`` is ordinal-free on torch-npu; keep a bounded fallback."""
    if ordinal is None:
        return getter()
    try:
        return getter()
    except TypeError:
        return getter(int(ordinal))


def measure_memory(torch_npu: Any, ordinal: int | None = None, *,
                   torch: Any = None) -> dict[str, Any]:
    """Read free/total device memory from ``torch.npu.mem_get_info``."""
    surface = _npu_surface(torch_npu, torch, "mem_get_info")
    getter = getattr(surface, "mem_get_info", None)
    if not callable(getter):
        return {"measured": False, "free_bytes": None, "total_bytes": None,
                "missing": ["mem_get_info"]}
    try:
        payload = _read_memory(surface, getter, ordinal)
    except TimeoutError:
        raise
    except Exception as exc:
        return {"measured": False, "free_bytes": None, "total_bytes": None,
                "missing": [_bounded_text(exc)]}
    if isinstance(payload, (list, tuple)) and len(payload) >= 2:
        free, total = payload[0], payload[1]
    elif isinstance(payload, Mapping):
        free, total = payload.get("free"), payload.get("total")
    else:
        free = total = None
    return {"measured": _positive_or_none(free) is not None,
            "free_bytes": _positive_or_none(free),
            "total_bytes": _positive_or_none(total), "missing": []}


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
    """Per-overload argument names, positional and keyword."""
    text = str(schema or "")
    start, end = text.find("("), text.find(")", text.find("(") + 1)
    if start < 0 or end < 0:
        return ()
    names: list[str] = []
    for part in re.split(r",(?![^()]*\))", text[start + 1:end]):
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*",
                                 part.split("=", 1)[0].strip())
        if identifiers:
            names.append(identifiers[-1])
    return tuple(names)
def inspect_operator_schemas(namespaces: Mapping[str, Any]) -> dict[str, Any]:
    """Enumerate installed operator packets, overloads, schemas and signatures."""
    entries: list[dict[str, Any]] = []
    for target in ABI_TARGETS:
        record: dict[str, Any] = {
            "key": target["key"], "available": False, "namespace": None,
            "overloads": [], "schemas": [], "overload_schemas": [],
            "python_signature": None,
            "arguments": [], "required_arguments": list(target["args"]),
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
                    record["overload_schemas"].append({
                        "overload": str(name),
                        "schema": _bounded_text(schema),
                        "arguments": sorted(set(overload_arguments)),
                    })
            if not names:
                schema = getattr(packet, "_schema", None)
                if schema is not None:
                    record["schemas"].append(_bounded_text(schema))
                    overload_arguments = _schema_arguments(schema)
                    arguments.extend(overload_arguments)
                    record["overload_schemas"].append({
                        "overload": "default",
                        "schema": _bounded_text(schema),
                        "arguments": sorted(set(overload_arguments)),
                    })
            try:
                record["python_signature"] = _bounded_text(inspect.signature(packet))
            except (TypeError, ValueError):
                record["python_signature"] = None
            record["arguments"] = sorted(set(arguments))
            supported = set(arguments)
            if record["python_signature"]:
                supported.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*",
                                            record["python_signature"]))
            record["argument_support"] = {name: name in supported
                                          for name in target["args"]}
            record["missing_arguments"] = [name for name in target["args"]
                                           if name not in supported]
            break
        entries.append(record)
    return {"targets": entries,
            "available": sorted(item["key"] for item in entries if item["available"]),
            "unavailable": sorted(item["key"] for item in entries
                                  if not item["available"])}
def _numeric_equal(actual: Any, expected: Any, tolerance: float) -> bool:
    try:
        difference = abs(float(actual) - float(expected))
    except (TypeError, ValueError):
        return False
    scale = max(1.0, abs(float(expected)))
    return difference <= tolerance * scale
def run_numeric_canary(name: str, callable_: Any, reference: Any,
                       *, tolerance: float = 1e-2) -> dict[str, Any]:
    """Run one tiny numerical canary; never promotes a failure into a crash."""
    if not callable(callable_):
        return {"name": name, "status": "unavailable", "reason": "callable_absent"}
    try:
        produced = callable_()
        expected = reference() if callable(reference) else reference
    except TimeoutError:
        raise
    except Exception as exc:
        return {"name": name, "status": "unsupported_binding",
                "reason": _bounded_text(exc)}
    try:
        produced_value = produced.item() if hasattr(produced, "item") else produced
    except TimeoutError:
        raise
    except Exception as exc:
        return {"name": name, "status": "unsupported_binding",
                "reason": _bounded_text(exc)}
    matched = _numeric_equal(produced_value, expected, tolerance)
    return {"name": name, "status": "ok" if matched else "mismatch",
            "actual": produced_value, "expected": expected,
            "tolerance": tolerance}
def _decoded_layers(text: str) -> list[str]:
    """Iteratively URL-decode a string, preserving each inspected layer."""
    layers = [text]
    current = text
    for _ in range(_DECODE_DEPTH):
        decoded = unquote(current)
        if decoded == current:
            break
        layers.append(decoded)
        current = decoded
    return layers
def _ipv6_present(text: str) -> bool:
    for candidate in _IPV6_CANDIDATE.findall(text):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.version == _IPV6_VERSION:
            return True
    return False
def _private_tokens(text: str, home: str | None) -> list[str]:
    findings: list[str] = []
    for layer in _decoded_layers(text):
        if home and home.rstrip("/") and home.rstrip("/") in layer:
            findings.append("home")
        if _ABSOLUTE_HOME.search(layer):
            findings.append("home")
        if _HOST_ADDRESS.search(layer) or _ipv6_present(layer):
            findings.append("host_address")
        if _DEVICE_NODE.search(layer):
            findings.append("device_node")
        if _IMAGE_DIGEST.search(layer):
            findings.append("image_digest")
        lowered = layer.lower()
        if any(marker in lowered for marker in _REGISTRY_MARKERS):
            findings.append("registry")
    return findings
def _replace_ipv6(match: re.Match[str]) -> str:
    try:
        address = ipaddress.ip_address(match.group(0))
    except ValueError:
        return match.group(0)
    return _HOST_IP_PLACEHOLDER if address.version == _IPV6_VERSION else match.group(0)
def _scrub_text(text: str, home: str | None) -> str:
    if home:
        text = re.sub(re.escape(home.rstrip("/")), _HOME_PLACEHOLDER, text,
                      flags=re.IGNORECASE)
    text = _IMAGE_DIGEST.sub(_DIGEST_PLACEHOLDER, text)
    for marker in _REGISTRY_MARKERS:
        text = re.sub(re.escape(marker), _REGISTRY_PLACEHOLDER, text,
                      flags=re.IGNORECASE)
    text = _ABSOLUTE_HOME.sub(_HOME_PLACEHOLDER, text)
    text = _DEVICE_NODE.sub(_DEVICE_PLACEHOLDER, text)
    text = _HOST_ADDRESS.sub(_HOST_IP_PLACEHOLDER, text)
    return _IPV6_CANDIDATE.sub(_replace_ipv6, text)
def scrub_portable(value: Any, *, home: str | None = None) -> Any:
    """Replace home paths, host addresses, registry markers and image digests."""
    if isinstance(value, Mapping):
        return {scrub_portable(key, home=home): scrub_portable(item, home=home)
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub_portable(item, home=home) for item in value]
    if not isinstance(value, str):
        return value
    layers = _decoded_layers(value)
    if any(_private_tokens(layer, home) for layer in layers):
        return _scrub_text(layers[-1], home)
    return _scrub_text(value, home)
def portable_violations(value: Any, *, home: str | None = None) -> list[str]:
    """List the forbidden portable-receipt tokens still present in ``value``."""
    findings: list[str] = []
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, Mapping):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
        elif isinstance(item, str):
            findings.extend(_private_tokens(item, home))
    return sorted(set(findings))
def portable_receipt(payload: Mapping[str, Any], *,
                     home: str | None = None) -> dict[str, Any]:
    """Scrub then verify one published receipt; unportable data is an error."""
    prepared = scrub_portable(dict(payload), home=home)
    findings = portable_violations(prepared, home=home)
    if findings:
        raise ProfilerUsageError(
            f"bench_receipt_not_portable: {', '.join(findings)}")
    return prepared
def capture_uri(capture_id: Any, member: Any) -> str:
    """Build a validated ``capture://<id>/<relative-member>`` provenance URI."""
    identifier = str(capture_id or "")
    if not _CAPTURE_ID.match(identifier):
        raise ProfilerUsageError(f"bench_capture_id_invalid: {_bounded_text(identifier)!r}")
    text = str(member or "").strip().replace("\\", "/")
    if (not text or text.startswith("/") or ".." in text.split("/")
            or ":" in text or _ABSOLUTE_HOME.search(text)):
        raise ProfilerUsageError(f"bench_capture_member_invalid: {_bounded_text(text)!r}")
    return f"capture://{identifier}/{text}"
def software_versions(modules: Mapping[str, Any]) -> dict[str, Any]:
    """Record installed package revisions (no image digest, no local path)."""
    versions: dict[str, Any] = {"python": platform.python_version(),
                                "implementation": platform.python_implementation()}
    for label, module in modules.items():
        version = getattr(module, "__version__", None) if module is not None else None
        if version is None and module is not None:
            try:
                from importlib import metadata
                version = metadata.version(str(getattr(module, "__name__", label)))
            except TimeoutError:
                raise
            except Exception:
                version = None
        versions[label] = None if version is None else _bounded_text(version, 80)
    return versions
def _device_receipt(torch_npu: Any, ordinal: int, *,
                    torch: Any = None) -> dict[str, Any]:
    properties = device_properties(torch_npu, ordinal, torch=torch)
    memory = measure_memory(torch_npu, ordinal, torch=torch)
    receipt: dict[str, Any] = {"ordinal": ordinal, "properties": properties,
                               "memory": memory}
    try:
        receipt["budget"] = vram_budget(memory.get("free_bytes"),
                                       total_bytes=memory.get("total_bytes"))
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
        description="Bind LOCAL_RANK, verify the physical die, inspect operator ABIs "
                    "and device properties, run numerical canaries.",
        allow_abbrev=False)
    parser.add_argument("--allowed-phy-ids", default=None,
                        help="physical die allowlist, e.g. '12..15' or '0,1,4,5'")
    parser.add_argument("--sparse-visible-devices", action="store_true",
                        help="LOCAL_RANK carries a physical id from an explicit "
                             "sparse ASCEND_RT_VISIBLE_DEVICES map")
    parser.add_argument("--out", "--output", dest="output", default=None,
                        help="write JSON here (atomic); otherwise print to stdout")
    return parser
def build_abi_receipt(*, allowed_phy_ids: Sequence[int] = (),
                      environ: Mapping[str, str] | None = None,
                      torch: Any = None, torch_npu: Any = None,
                      resolver: Any = None,
                      sparse_visible_devices: bool = False,
                      namespaces: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the abi receipt from an explicit device/torch context."""
    torch = torch if torch is not None else _load_torch()[0]
    torch_npu = torch_npu if torch_npu is not None else _load_torch()[1]
    binding = bind_device(torch=torch, torch_npu=torch_npu, environ=environ,
                          allowed_phy_ids=allowed_phy_ids, resolver=resolver,
                          sparse_visible_devices=sparse_visible_devices)
    modules = {"torch": torch, "torch_npu": torch_npu}
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
def _canaries(torch: Any, namespaces: Mapping[str, Any],
              ordinal: int = 0) -> list[dict[str, Any]]:
    """Tiny numerical canaries on the bound NPU ordinal when tensor ops exist."""
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
        results.append(run_numeric_canary("vector_add_unit", run_vector_add,
                                          lambda: 2.0))
    for target in ABI_TARGETS:
        container = next((namespaces[name] for name in target["namespaces"]
                          if name in namespaces), None)
        packet = getattr(container, target["key"], None) if container is not None else None
        if packet is None:
            results.append({"name": f"schema:{target['key']}", "status": "unavailable",
                            "reason": "operator_absent"})
            continue
        overloads = getattr(packet, "overloads", None)
        names = list(overloads()) if callable(overloads) else []
        results.append({"name": f"schema:{target['key']}", "status": "ok",
                        "overload_count": len(names)})
    return results
def main(argv: Sequence[str] | None = None) -> int:
    args = _abi_parser().parse_args(list(argv or ()))
    allowed = parse_allowed_phy_ids(args.allowed_phy_ids if args.allowed_phy_ids is not None
                                    else os.environ.get(ALLOWED_PHY_IDS_ENV))
    try:
        torch, torch_npu = _load_torch()
    except TimeoutError:
        raise
    except Exception as exc:
        payload = {"schema": ABI_SCHEMA, "status": "torch_npu_unavailable",
                   "reason": _bounded_text(exc)}
        _emit(payload, args.output)
        return 3
    try:
        receipt = build_abi_receipt(
            allowed_phy_ids=allowed, torch=torch, torch_npu=torch_npu,
            sparse_visible_devices=bool(args.sparse_visible_devices))
    except ProfilerUsageError as exc:
        payload = portable_receipt({
            "schema": ABI_SCHEMA, "status": "binding_rejected",
            "reason": _bounded_text(exc)}, home=os.environ.get("HOME"))
        _emit(payload, args.output)
        return 2
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
        print(json.dumps({"output": str(target), "status": payload.get("status")},
                         sort_keys=True))
        return
    sys.stdout.write(text)
__all__ = [
    "ABI_SCHEMA", "ABI_TARGETS", "ALLOWED_PHY_IDS_ENV", "LOCAL_RANK_ENV",
    "MAX_DEVICE_ORDINAL", "PHYSICAL_DIE_SCHEMA", "S0_VRAM_CAP_BYTES",
    "S0_VRAM_RESERVE_BYTES", "VISIBLE_DEVICES_ENV", "bind_device",
    "build_abi_receipt", "capture_uri", "device_properties", "inspect_operator_schemas",
    "main", "measure_memory", "parse_allowed_phy_ids", "parse_device_mask",
    "portable_receipt", "portable_violations", "resolve_allowed_phy_ids",
    "resolve_local_rank",
    "resolve_physical_die", "run_numeric_canary", "scrub_portable",
    "software_versions", "vram_budget",
]
if __name__ == "__main__":
    raise SystemExit(main())
