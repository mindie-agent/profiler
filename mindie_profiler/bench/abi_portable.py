"""Portable receipt scrubbing, capture URIs and software version helpers.

[Role]
  Scrub and verify portable JSON receipts for the ``bench`` suite (removing
  ``$HOME``, host IPv4/IPv6 addresses, ``/dev/davinci*`` nodes, container
  registry prefixes and image digests), construct ``capture://`` URIs and
  collect installed software package versions.

[Invariants]
  * ``portable_receipt`` scrubs up to ``_DECODE_DEPTH`` URL-encoded layers and
    fails closed if any forbidden token remains.
  * ``capture_uri`` rejects absolute paths, ``..`` segments, schemes and home
    markers.

[Timeouts & Locks]
  Pure in-memory string/tree processing; no locks or threads.

[Side-Effect Policy]
  Returns fresh dicts/lists/strings; mutates no caller containers.
"""

from __future__ import annotations

import ipaddress
import platform
import re
from typing import Any, Mapping
from urllib.parse import unquote

from ..events import ProfilerUsageError
from .profiles import profile_section

_CFG = profile_section("abi")
MAX_DIAGNOSTIC_CHARS = int(_CFG["max_diagnostic_chars"])
_DECODE_DEPTH = int(_CFG["decode_depth"])
_IPV6_VERSION = int(_CFG["ipv6_version"])
_VER_MAX_CHARS = int(_CFG["version_max_chars"])

_DOCKER_REGISTRY = "docker" + ".io/"
_SWR_REGISTRY = "swr" + ".cn-"
_QUAY_REGISTRY = "quay" + ".io/"
_REGISTRY_MARKERS = (_DOCKER_REGISTRY, _SWR_REGISTRY, _QUAY_REGISTRY)
_DIGEST_MARKER = "@sha" + "256:"
_HOST_ADDRESS = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_IPV6_CANDIDATE = re.compile(
    r"(?<![\w:.])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:.])"
)
_DEVICE_NODE = re.compile(r"/dev/davinci[0-9A-Za-z_]*")
_IMAGE_DIGEST = re.compile("(?i)" + re.escape(_DIGEST_MARKER) + r"[0-9a-f]{64}")
_USERS_PREFIX = "/" + r"Users/[^/\s\"']+"
_VOLUMES_PREFIX = "/" + r"Volumes/[^\s\"']+"
_ABSOLUTE_HOME = re.compile(
    r"(?:/home/[^/\s\"']+|"
    + _USERS_PREFIX
    + "|"
    + _VOLUMES_PREFIX
    + r"|/mnt/[^\s\"']+|/root(?:/[^\s\"']*)?|\$\{?HOME\}?|~/)"
)
_CAPTURE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_HOST_IP_PLACEHOLDER = "<host-address>"
_DEVICE_PLACEHOLDER = "<device-node>"
_DIGEST_PLACEHOLDER = "@<image-digest>"
_HOME_PLACEHOLDER = "<home>"
_REGISTRY_PLACEHOLDER = "<registry>/"
_VERSION_EXEMPT_KEYS = frozenset({
    "cann_version",
    "cann_innerversion",
    "driver_version",
    "torch_version",
    "torch_npu_version",
    "triton_version",
    "profiler_version",
    "version",
    "cann_packages",
    "custom_op_libs",
    "env_fingerprint_id",
    "base_env_fingerprint_id",
    "cand_env_fingerprint_id",
    "bucket_relpath",
})
_DOTTED_VERSION_RE = re.compile(
    r"^(?:(?:wheel:)?\d+(?:\.\d+){2,3}(?:[A-Za-z0-9._+-]*)?|(?:buckets/)?env-[a-z0-9_]+-cann[a-z0-9._-]+-[0-9a-f]{16})$"
)
FORBIDDEN_CALLER_PREDICTION_KEYS = frozenset({
    "sim_reference",
    "predicted_ns",
    "predicted_us",
    "predicted_ms",
    "predicted_s",
    "predicted_duration",
})
_PREDICTED_PREFIX = "predicted_"


def _bounded(value: Any, limit: int = MAX_DIAGNOSTIC_CHARS) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _decoded_layers(text: str) -> list[str]:
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


def _private_tokens(text: str, home: str | None, *, allow_version_dotted: bool = False) -> list[str]:
    findings: list[str] = []
    for layer in _decoded_layers(text):
        if home and home.rstrip("/") and home.rstrip("/") in layer:
            findings.append("home")
        if _ABSOLUTE_HOME.search(layer):
            findings.append("home")
        version_like = allow_version_dotted and bool(_DOTTED_VERSION_RE.match(layer.strip()))
        if (not version_like and _HOST_ADDRESS.search(layer)) or _ipv6_present(layer):
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


def _scrub_text(text: str, home: str | None, *, allow_version_dotted: bool = False) -> str:
    if home:
        text = re.sub(re.escape(home.rstrip("/")), _HOME_PLACEHOLDER, text, flags=re.IGNORECASE)
    text = _IMAGE_DIGEST.sub(_DIGEST_PLACEHOLDER, text)
    for marker in _REGISTRY_MARKERS:
        text = re.sub(re.escape(marker), _REGISTRY_PLACEHOLDER, text, flags=re.IGNORECASE)
    text = _ABSOLUTE_HOME.sub(_HOME_PLACEHOLDER, text)
    text = _DEVICE_NODE.sub(_DEVICE_PLACEHOLDER, text)
    if not (allow_version_dotted and _DOTTED_VERSION_RE.match(text.strip())):
        text = _HOST_ADDRESS.sub(_HOST_IP_PLACEHOLDER, text)
    return _IPV6_CANDIDATE.sub(_replace_ipv6, text)


def scrub_portable(value: Any, *, home: str | None = None, _allow_version: bool = False) -> Any:
    """Replace home paths, host addresses, registry markers and image digests."""
    if isinstance(value, Mapping):
        return {
            scrub_portable(key, home=home): scrub_portable(
                item,
                home=home,
                _allow_version=_allow_version or (isinstance(key, str) and key in _VERSION_EXEMPT_KEYS),
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [scrub_portable(item, home=home, _allow_version=_allow_version) for item in value]
    if not isinstance(value, str):
        return value
    layers = _decoded_layers(value)
    if any(_private_tokens(layer, home, allow_version_dotted=_allow_version) for layer in layers):
        return _scrub_text(layers[-1], home, allow_version_dotted=_allow_version)
    return _scrub_text(value, home, allow_version_dotted=_allow_version)


def portable_violations(value: Any, *, home: str | None = None) -> list[str]:
    """List the forbidden portable-receipt tokens still present in ``value``."""
    findings: list[str] = []
    pending: list[tuple[Any, bool]] = [(value, False)]
    while pending:
        item, allow_ver = pending.pop()
        if isinstance(item, Mapping):
            for key, val in item.items():
                pending.append((key, False))
                pending.append((val, allow_ver or (isinstance(key, str) and key in _VERSION_EXEMPT_KEYS)))
        elif isinstance(item, (list, tuple)):
            pending.extend((child, allow_ver) for child in item)
        elif isinstance(item, str):
            findings.extend(_private_tokens(item, home, allow_version_dotted=allow_ver))
    return sorted(set(findings))


def _is_forbidden_prediction_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    lowered = key.strip().lower()
    return lowered in FORBIDDEN_CALLER_PREDICTION_KEYS or lowered.startswith(_PREDICTED_PREFIX)


def forbidden_prediction_keys(value: Any) -> list[str]:
    """Return sorted forbidden caller-prediction keys found anywhere in ``value``."""
    found: list[str] = []
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, Mapping):
            for key, child in item.items():
                if _is_forbidden_prediction_key(key):
                    found.append(str(key))
                pending.append(child)
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
    return sorted(set(found))


def strip_caller_predictions(value: Any) -> Any:
    """Return a fresh tree with ``sim_reference`` and ``predicted_*`` keys removed."""
    if isinstance(value, Mapping):
        return {
            key: strip_caller_predictions(child)
            for key, child in value.items()
            if not _is_forbidden_prediction_key(key)
        }
    if isinstance(value, list):
        return [strip_caller_predictions(item) for item in value]
    if isinstance(value, tuple):
        return [strip_caller_predictions(item) for item in value]
    return value


def portable_receipt(
    payload: Mapping[str, Any], *, home: str | None = None
) -> dict[str, Any]:
    """Scrub then verify one published receipt; unportable or leaked prediction data fails closed."""
    leaked = forbidden_prediction_keys(payload)
    if leaked:
        raise ProfilerUsageError(
            f"bench_receipt_forbidden_prediction_keys: {', '.join(leaked)}"
        )
    prepared = scrub_portable(dict(payload), home=home)
    findings = portable_violations(prepared, home=home)
    if findings:
        raise ProfilerUsageError(f"bench_receipt_not_portable: {', '.join(findings)}")
    return prepared


def capture_uri(capture_id: Any, member: Any) -> str:
    """Build a validated ``capture://<id>/<relative-member>`` provenance URI."""
    identifier = str(capture_id or "")
    if not _CAPTURE_ID.match(identifier):
        raise ProfilerUsageError(f"bench_capture_id_invalid: {_bounded(identifier)!r}")
    text = str(member or "").strip().replace("\\", "/")
    if (
        not text
        or text.startswith("/")
        or ".." in text.split("/")
        or ":" in text
        or _ABSOLUTE_HOME.search(text)
    ):
        raise ProfilerUsageError(f"bench_capture_member_invalid: {_bounded(text)!r}")
    return f"capture://{identifier}/{text}"


def software_versions(modules: Mapping[str, Any]) -> dict[str, Any]:
    """Record installed package revisions (no image digest, no local path)."""
    versions: dict[str, Any] = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
    }
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
        versions[label] = None if version is None else _bounded(version, _VER_MAX_CHARS)
    return versions


__all__ = [
    "FORBIDDEN_CALLER_PREDICTION_KEYS",
    "capture_uri",
    "forbidden_prediction_keys",
    "portable_receipt",
    "portable_violations",
    "scrub_portable",
    "software_versions",
    "strip_caller_predictions",
]
