"""Content-addressed incremental benchmark campaign store with immutable shards.

[Role]
  Compute the byte-identical 31-field ``CanonicalKernelKey`` digest shared with
  ``mindie_sim.schema.bench_matrix``, manage version-fingerprinted campaign
  buckets under ``buckets/<env_fingerprint_id>/``, persist immutable per-run
  observation shards (``runs/<run_id>.jsonl``), atomically update ``index.json``
  and ``campaign_index.json`` under ``storage_locks.exclusive_lock``, preserve
  cache-hit lineage, enforce ``Never-Overwrite-Qualified``, and enforce
  heldout-vs-training geometry independence (``training_manifest_sha256``).

[Invariants]
  * Pure CPU (``DEV-ZERO-CTX``); zero ``torch``, ``torch_npu``, or
    ``mindie_sim`` imports.
  * ``canonical_key_digest`` uses the exact 31-field fixed schema and compact
    ASCII JSON (``allow_nan=False``) shared with ``mindie-sim``.
  * Per-run observation shards ``runs/<run_id>.jsonl`` are write-once immutable
    so later runs never mutate or invalidate prior campaign checksums.
  * ``Never-Overwrite-Qualified``: an unqualified or ``host_fallback`` record
    never overwrites an existing ``qualified=True`` entry in ``index.json``.
  * Heldout lookup rejects any geometry present in the frozen training manifest.

[Timeouts & Locks]
  Serializes bucket mutations via ``storage_locks.exclusive_lock`` on
  ``.bucket.lock`` and ``.campaign.lock``; publishes metadata atomically via
  ``os.replace``.

[Side-Effect Policy]
  Writes strictly inside the caller-supplied ``campaign_dir``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from ..events import ProfilerUsageError
from ..storage_locks import exclusive_lock
from .abi_portable import FORBIDDEN_CALLER_PREDICTION_KEYS, portable_receipt
from .env_fingerprint import (
    ENV_SCHEMA,
    compute_env_fingerprint_id,
    infer_soc_arch,
    is_live_clock_source,
    validate_clock_band,
)
from .observations import ObservationJournal
from .profiles import profile_section

PLAN_V2_SCHEMA = "mindie-bench-plan/2"
CAMPAIGN_SCHEMA = "mindie-bench-campaign/1"
BUCKET_INDEX_SCHEMA = "mindie-bench-bucket-index/1"
CAMPAIGN_INDEX_SCHEMA = "mindie-bench-campaign-index/1"

_CAMPAIGN_CFG = profile_section("campaign")
_SIG_VERSION = int(_CAMPAIGN_CFG["sig_version"])
_DIGEST_CHARS = int(_CAMPAIGN_CFG["digest_chars"])
_HASH_CHUNK_BYTES = int(_CAMPAIGN_CFG["hash_chunk_bytes"])
_JOURNAL_MODE = int(_CAMPAIGN_CFG["journal_mode"])

_FORBIDDEN_KEY_FIELDS = frozenset({
    "model_id",
    "layer_idx",
    "split",
    "run_id",
    "seq_len_label",
    "concurrency_label",
    "plan_id",
    "case_id",
    *FORBIDDEN_CALLER_PREDICTION_KEYS,
})
_VALID_KINDS = frozenset({"operator", "subgraph", "collective"})
_VALID_CAPTURE_MODES = frozenset({"eager", "aclgraph"})
_VALID_RESIDENCIES = frozenset({"cold_hbm", "warm_l2"})
_RESIDENCY_ALIASES = {
    "cold_hbm": "cold_hbm",
    "cold_ring": "cold_hbm",
    "dram": "cold_hbm",
    "device": "cold_hbm",
    "warm_l2": "warm_l2",
    "hot_control": "warm_l2",
    "l2": "warm_l2",
}

CANONICAL_KEY_FIELDS: tuple[str, ...] = (
    "sig_version",
    "kind",
    "sku",
    "soc_arch",
    "abi_backend",
    "upstream_abi",
    "bench_builder",
    "canonical_shapes",
    "strides",
    "storage_offsets",
    "dtypes",
    "layouts",
    "kv_allocator_block_size",
    "kv_kernel_block_size",
    "cp_kv_cache_interleave_size",
    "page_geometry",
    "per_expert_token_counts",
    "per_rank_token_counts",
    "capture_mode",
    "aclgraph_padded_bucket",
    "workspace_policy",
    "stream_dependencies",
    "residency",
    "quant_meta",
    "op_attrs",
    "ordered_rank_placement",
    "link_tiers",
    "collective_algorithm",
    "split_sizes",
    "timed_nodes",
    "edges",
)


def canonical_json(obj: Any) -> bytes:
    """Deterministic UTF-8 compact JSON encoding (no trailing newline, NaN forbidden)."""
    try:
        text = json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        raise ProfilerUsageError(f"bench_canonical_json_invalid: {exc}") from exc
    return text.encode("utf-8")


def sha256_canonical(obj: Any) -> str:
    """Return full 64-hex SHA-256 of ``canonical_json(obj)``."""
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def seal_payload(
    payload: Mapping[str, Any],
    seal_field: str,
    *,
    exclude_fields: Sequence[str] | frozenset[str] = (),
) -> dict[str, Any]:
    """Return a copy of ``payload`` sealed with ``seal_field = sha256(canonical_json(body))``."""
    excluded = {seal_field, *(str(item) for item in exclude_fields)}
    body = {k: v for k, v in payload.items() if k not in excluded}
    sealed = dict(payload)
    sealed[seal_field] = sha256_canonical(body)
    return sealed


def verify_seal(
    payload: Mapping[str, Any],
    seal_field: str,
    *,
    exclude_fields: Sequence[str] | frozenset[str] = (),
) -> bool:
    """Verify ``payload[seal_field]`` equals ``sha256(canonical_json(without_excluded))``."""
    declared = payload.get(seal_field)
    if not isinstance(declared, str) or not declared:
        return False
    excluded = {seal_field, *(str(item) for item in exclude_fields)}
    body = {k: v for k, v in payload.items() if k not in excluded}
    return sha256_canonical(body) == declared


CASE_RAW_SHA256_EXCLUDED_FIELDS: frozenset[str] = frozenset({"raw_sha256", "cache_status", "split"})


def seal_case_raw_sha256(case_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Seal a campaign case record with ``raw_sha256`` matching ``mindie_sim.schema.bench_matrix``."""
    return seal_payload(case_payload, "raw_sha256", exclude_fields=CASE_RAW_SHA256_EXCLUDED_FIELDS)


def verify_case_raw_sha256(case_payload: Mapping[str, Any]) -> bool:
    """Verify ``raw_sha256`` on a measured or cache-hit campaign case record."""
    return verify_seal(case_payload, "raw_sha256", exclude_fields=CASE_RAW_SHA256_EXCLUDED_FIELDS)


def _opt_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProfilerUsageError(f"bench_canonical_key_int_invalid: {value!r}")
    return int(value)


def _opt_int_list(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ProfilerUsageError(f"bench_canonical_key_list_invalid: {value!r}")
    out: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ProfilerUsageError(f"bench_canonical_key_int_invalid: {item!r}")
        out.append(int(item))
    return out


def _opt_str_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ProfilerUsageError(f"bench_canonical_key_list_invalid: {value!r}")
    return [str(item) for item in value]


def _normalize_strides(raw: Any) -> dict[str, list[int]]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ProfilerUsageError("bench_canonical_key_strides_invalid")
    result: dict[str, list[int]] = {}
    for name, dims in sorted(raw.items()):
        parsed = _opt_int_list(dims)
        result[str(name)] = [] if parsed is None else parsed
    return result


def _normalize_offsets(raw: Any) -> dict[str, int]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ProfilerUsageError("bench_canonical_key_offsets_invalid")
    result: dict[str, int] = {}
    for name, val in sorted(raw.items()):
        parsed = _opt_int(val)
        if parsed is None:
            raise ProfilerUsageError("bench_canonical_key_offsets_invalid")
        result[str(name)] = parsed
    return result


def normalize_canonical_key(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and emit the exact fixed 31-field ``CanonicalKernelKey`` mapping."""
    if not isinstance(raw, Mapping):
        raise ProfilerUsageError("bench_canonical_key_invalid: expected mapping")
    allowed = frozenset(CANONICAL_KEY_FIELDS)
    for key in raw:
        key_str = str(key)
        if key_str in _FORBIDDEN_KEY_FIELDS or key_str.lower().startswith("predicted_"):
            raise ProfilerUsageError(f"bench_canonical_key_forbidden_field: {key_str}")
        if key_str not in allowed:
            raise ProfilerUsageError(f"bench_canonical_key_unknown_field: {key_str}")
    sig_version = int(raw.get("sig_version", _SIG_VERSION))
    if sig_version != _SIG_VERSION:
        raise ProfilerUsageError(f"bench_canonical_key_sig_version_invalid: {sig_version}")
    raw_kind = str(raw.get("kind") or "operator").strip().lower()
    kind = "collective" if raw_kind == "fabric" else raw_kind
    if kind not in _VALID_KINDS:
        raise ProfilerUsageError(f"bench_canonical_key_kind_invalid: {raw_kind!r}")
    capture_mode = str(raw.get("capture_mode") or "eager").strip().lower()
    if capture_mode not in _VALID_CAPTURE_MODES:
        raise ProfilerUsageError(f"bench_canonical_key_capture_mode_invalid: {capture_mode!r}")
    raw_res = str(raw.get("residency") or "cold_hbm").strip().lower()
    residency = _RESIDENCY_ALIASES.get(raw_res, raw_res)
    if residency not in _VALID_RESIDENCIES:
        raise ProfilerUsageError(f"bench_canonical_key_residency_invalid: {raw_res!r}")
    sku = str(raw.get("sku") or "").strip()
    soc_arch = str(raw.get("soc_arch") or infer_soc_arch(sku)).strip().upper()
    raw_timed = raw.get("timed_nodes")
    timed_nodes = (
        [normalize_canonical_key(node) if isinstance(node, Mapping) and "sig_version" in node else dict(node) for node in raw_timed]
        if isinstance(raw_timed, (list, tuple))
        else None
    )
    raw_edges = raw.get("edges")
    edges = [list(edge) if isinstance(edge, (list, tuple)) else edge for edge in raw_edges] if isinstance(raw_edges, (list, tuple)) else None
    raw_stream_deps = raw.get("stream_dependencies")
    stream_deps = (
        [list(item) if isinstance(item, (list, tuple)) else [item] for item in raw_stream_deps]
        if isinstance(raw_stream_deps, (list, tuple))
        else []
    )
    return {
        "sig_version": _SIG_VERSION,
        "kind": kind,
        "sku": sku,
        "soc_arch": soc_arch,
        "abi_backend": str(raw.get("abi_backend") or "").strip().lower(),
        "upstream_abi": str(raw.get("upstream_abi") or ""),
        "bench_builder": str(raw.get("bench_builder") or ""),
        "canonical_shapes": dict(raw.get("canonical_shapes") or {}) if isinstance(raw.get("canonical_shapes"), Mapping) else {},
        "strides": _normalize_strides(raw.get("strides")),
        "storage_offsets": _normalize_offsets(raw.get("storage_offsets")),
        "dtypes": {str(k): str(v) for k, v in sorted((raw.get("dtypes") or {}).items())} if isinstance(raw.get("dtypes"), Mapping) else {},
        "layouts": {str(k): str(v) for k, v in sorted((raw.get("layouts") or {}).items())} if isinstance(raw.get("layouts"), Mapping) else {},
        "kv_allocator_block_size": _opt_int(raw.get("kv_allocator_block_size")),
        "kv_kernel_block_size": _opt_int(raw.get("kv_kernel_block_size")),
        "cp_kv_cache_interleave_size": _opt_int(raw.get("cp_kv_cache_interleave_size")),
        "page_geometry": dict(raw["page_geometry"]) if isinstance(raw.get("page_geometry"), Mapping) else None,
        "per_expert_token_counts": _opt_int_list(raw.get("per_expert_token_counts")),
        "per_rank_token_counts": _opt_int_list(raw.get("per_rank_token_counts")),
        "capture_mode": capture_mode,
        "aclgraph_padded_bucket": _opt_int(raw.get("aclgraph_padded_bucket")),
        "workspace_policy": str(raw.get("workspace_policy") or "default"),
        "stream_dependencies": stream_deps,
        "residency": residency,
        "quant_meta": dict(raw.get("quant_meta") or {}) if isinstance(raw.get("quant_meta"), Mapping) else {},
        "op_attrs": dict(raw.get("op_attrs") or {}) if isinstance(raw.get("op_attrs"), Mapping) else {},
        "ordered_rank_placement": _opt_int_list(raw.get("ordered_rank_placement")),
        "link_tiers": _opt_str_list(raw.get("link_tiers")),
        "collective_algorithm": None if raw.get("collective_algorithm") is None else str(raw.get("collective_algorithm")),
        "split_sizes": _opt_int_list(raw.get("split_sizes")),
        "timed_nodes": timed_nodes,
        "edges": edges,
    }


def canonical_key_digest(key_payload: Mapping[str, Any]) -> str:
    """Compute the 16-hex SHA-256 canonical key digest."""
    normalized = normalize_canonical_key(key_payload)
    return hashlib.sha256(canonical_json(normalized)).hexdigest()[:_DIGEST_CHARS]


def canonical_case_id(key_payload: Mapping[str, Any]) -> str:
    """Return ``k2-<canonical_key_digest>``."""
    return f"k2-{canonical_key_digest(key_payload)}"


def verify_case_canonical_key(case: Mapping[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Recompute and verify ``canonical_key_digest`` and ``case_id`` for a v2 case."""
    raw_key = case.get("canonical_key")
    if not isinstance(raw_key, Mapping):
        raise ProfilerUsageError("bench_canonical_key_missing")
    normalized = normalize_canonical_key(raw_key)
    digest = hashlib.sha256(canonical_json(normalized)).hexdigest()[:_DIGEST_CHARS]
    expected_id = f"k2-{digest}"
    declared_digest = case.get("canonical_key_digest")
    if declared_digest is not None and str(declared_digest) != digest:
        raise ProfilerUsageError(
            f"bench_canonical_key_digest_mismatch: declared={declared_digest!r} computed={digest!r}"
        )
    declared_id = case.get("case_id")
    if isinstance(declared_id, str) and declared_id.startswith("k2-") and declared_id != expected_id:
        raise ProfilerUsageError(
            f"bench_canonical_key_digest_mismatch: case_id={declared_id!r} expected={expected_id!r}"
        )
    return digest, expected_id, normalized


def synthesize_canonical_key_from_v1_case(
    case: Mapping[str, Any],
    *,
    sku: str,
    soc_arch: str | None = None,
    capture_mode: str = "eager",
    residency: str = "cold_hbm",
) -> dict[str, Any]:
    """Deterministically build a 31-field ``CanonicalKernelKey`` for a v1 subgraph/op case."""
    nodes = [n for n in (case.get("nodes") or ()) if isinstance(n, Mapping)]
    primary = nodes[0] if nodes else case
    shape = dict(primary.get("shape") or {}) if isinstance(primary.get("shape"), Mapping) else {}
    raw_kind = str(case.get("kind") or ("subgraph" if len(nodes) > 1 else "operator")).lower()
    if raw_kind == "fabric" or primary.get("kind") == "collective":
        kind = "collective"
    elif len(nodes) > 1 or raw_kind == "subgraph":
        kind = "subgraph"
    else:
        kind = "operator"
    dtype = str(primary.get("dtype") or case.get("dtype") or "bf16")
    layout = str(primary.get("layout") or shape.get("layout") or case.get("layout") or "ND")
    block_size = shape.get("block_size")
    group_ranks = case.get("group_ranks") or primary.get("group_ranks")
    link_tiers = case.get("link_tiers") or ([str(case["route"])] if case.get("route") else None)
    timed_nodes: list[dict[str, Any]] | None = None
    edges: list[list[Any]] | None = None
    op_attrs = dict(case.get("op_attrs") or {})
    if kind == "subgraph":
        tb = case.get("timed_boundary") if isinstance(case.get("timed_boundary"), Mapping) else {}
        include_raw = tb.get("include")
        include_set = (
            {str(x) for x in include_raw}
            if isinstance(include_raw, (list, tuple, set, frozenset)) and include_raw
            else None
        )
        selected_nodes = [
            n for n in nodes if include_set is None or str(n.get("node_id") or "") in include_set
        ] or nodes
        timed_nodes = [
            {
                "node_id": str(n.get("node_id") or ""),
                "kind": str(n.get("kind") or "operator"),
                "builder": str(n.get("builder") or n.get("op") or ""),
                "upstream_abi": str(n.get("upstream_abi") or ""),
                "shape": dict(n.get("shape") or {}) if isinstance(n.get("shape"), Mapping) else {},
                "dtype": str(n.get("dtype") or dtype),
            }
            for n in selected_nodes
        ]
        edges = [
            [str(e.get("from") or ""), str(e.get("to") or ""), str(e.get("kind") or "data")]
            if isinstance(e, Mapping)
            else [str(x) for x in e]
            for e in (case.get("edges") or ())
            if isinstance(e, (Mapping, list, tuple))
        ]
        if include_set is not None:
            op_attrs["timed_boundary_include"] = sorted(include_set)
            op_attrs["all_graph_nodes"] = [str(n.get("node_id") or "") for n in nodes]
    return normalize_canonical_key({
        "sig_version": _SIG_VERSION,
        "kind": kind,
        "sku": sku,
        "soc_arch": soc_arch or infer_soc_arch(sku),
        "abi_backend": str(primary.get("abi_backend") or case.get("abi_backend") or "cann_aclnn"),
        "upstream_abi": str(primary.get("upstream_abi") or case.get("upstream_abi") or ""),
        "bench_builder": str(primary.get("builder") or case.get("builder") or primary.get("op") or case.get("op") or ""),
        "canonical_shapes": shape,
        "strides": primary.get("strides") or case.get("strides") or {},
        "storage_offsets": primary.get("storage_offsets") or case.get("storage_offsets") or {},
        "dtypes": {"input": dtype, "output": str(primary.get("output_dtype") or dtype)},
        "layouts": {"input": layout, "output": layout},
        "kv_allocator_block_size": int(block_size) if isinstance(block_size, int) and not isinstance(block_size, bool) else None,
        "kv_kernel_block_size": int(block_size) if isinstance(block_size, int) and not isinstance(block_size, bool) else None,
        "cp_kv_cache_interleave_size": case.get("cp_kv_cache_interleave_size"),
        "page_geometry": case.get("page_geometry") or primary.get("page_geometry"),
        "per_expert_token_counts": case.get("group_list") or primary.get("group_list"),
        "per_rank_token_counts": case.get("per_rank_token_counts"),
        "capture_mode": capture_mode,
        "aclgraph_padded_bucket": case.get("aclgraph_padded_bucket"),
        "workspace_policy": str(case.get("workspace_policy") or "default"),
        "stream_dependencies": case.get("stream_dependencies") or [],
        "residency": residency,
        "quant_meta": case.get("quant_meta") or {},
        "op_attrs": op_attrs,
        "ordered_rank_placement": list(group_ranks) if isinstance(group_ranks, (list, tuple)) else None,
        "link_tiers": list(link_tiers) if isinstance(link_tiers, (list, tuple)) else None,
        "collective_algorithm": case.get("collective_algorithm"),
        "split_sizes": case.get("send_splits") or case.get("split_sizes"),
        "timed_nodes": timed_nodes,
        "edges": edges,
    })


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def _file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_HASH_CHUNK_BYTES)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def stream_shards_sha256(base_dir: str | Path, shard_relpaths: Sequence[str]) -> str:
    """Compute canonical single- or multi-shard streaming SHA-256 matching ``mindie-sim``."""
    root = Path(base_dir)
    paths = [root / str(rel) for rel in shard_relpaths]
    if not paths:
        return hashlib.sha256(b"").hexdigest()
    hasher = hashlib.sha256()
    for shard_path in paths:
        with shard_path.open("rb") as handle:
            while True:
                chunk = handle.read(_HASH_CHUNK_BYTES)
                if not chunk:
                    break
                hasher.update(chunk)
    return hasher.hexdigest()


def index_entry_key(
    digest: str,
    capture_mode: str,
    residency: str,
    boundary: str = "device_kernel",
) -> str:
    """Stable lookup key inside ``index.json`` binding boundary alongside physical axes."""
    res = _RESIDENCY_ALIASES.get(str(residency).strip().lower(), str(residency).strip().lower())
    return f"{digest}|{capture_mode}|{res}|{boundary}"


def load_training_manifest_freeze(
    training_manifest: str | Path | Mapping[str, Any] | None,
) -> tuple[str | None, frozenset[str], frozenset[str]]:
    """Freeze training digests, geometry keys, and ``training_manifest_sha256``."""
    if training_manifest is None:
        return None, frozenset(), frozenset()
    if isinstance(training_manifest, Mapping):
        payload = dict(training_manifest)
    else:
        path = Path(training_manifest)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except TimeoutError:
            raise
        except (OSError, ValueError) as exc:
            raise ProfilerUsageError(f"bench_training_manifest_invalid: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ProfilerUsageError("bench_training_manifest_invalid: expected object")
    manifest_sha = sha256_canonical(payload)
    digests: set[str] = set()
    geoms: set[str] = set()
    for item in payload.get("canonical_key_digests") or ():
        if isinstance(item, str) and item:
            digests.add(item)
    for item in payload.get("geometry_keys") or ():
        if isinstance(item, str) and item:
            geoms.add(item)
    for bucket_key in ("cases", "blocked_cases"):
        for item in payload.get(bucket_key) or ():
            if not isinstance(item, Mapping):
                continue
            if item.get("split") == "heldout":
                continue
            digest = item.get("canonical_key_digest")
            if isinstance(digest, str) and digest:
                digests.add(digest)
            elif isinstance(item.get("canonical_key"), Mapping):
                digests.add(canonical_key_digest(item["canonical_key"]))
            gkey = item.get("geometry_key")
            if isinstance(gkey, str) and gkey:
                geoms.add(gkey)
    return manifest_sha, frozenset(digests), frozenset(geoms)


class CampaignStore:
    """Version-fingerprinted incremental bucket store with immutable per-run shards."""

    def __init__(self, campaign_dir: str | Path) -> None:
        self.root = Path(campaign_dir)
        self.buckets_dir = self.root / "buckets"
        self.root.mkdir(parents=True, exist_ok=True)
        self.buckets_dir.mkdir(parents=True, exist_ok=True)

    def bucket_dir(self, env_fingerprint_id: str) -> Path:
        return self.buckets_dir / str(env_fingerprint_id)

    def _bucket_lock(self, env_fingerprint_id: str) -> Path:
        bdir = self.bucket_dir(env_fingerprint_id)
        bdir.mkdir(parents=True, exist_ok=True)
        return bdir / ".bucket.lock"

    def _campaign_lock(self) -> Path:
        return self.root / ".campaign.lock"

    @staticmethod
    def _qualified_baseline_clock(
        env_receipt: Mapping[str, Any], nominal_clock_mhz: float | None
    ) -> float | None:
        obs = env_receipt.get("observed_clock_mhz")
        if obs is None or not is_live_clock_source(env_receipt.get("clock_source")):
            return None
        ok_band, _reason = validate_clock_band(obs, nominal_clock_mhz=nominal_clock_mhz)
        return float(obs) if ok_band else None

    def ensure_bucket(
        self,
        env_fingerprint: Mapping[str, Any],
        *,
        nominal_clock_mhz: float | None = None,
        home: str | None = None,
    ) -> dict[str, Any]:
        """Initialize or open a version-fingerprinted bucket atomically."""
        clean_env = portable_receipt(env_fingerprint, home=home)
        if clean_env.get("schema") != ENV_SCHEMA:
            clean_env["schema"] = ENV_SCHEMA
        computed_id = compute_env_fingerprint_id(clean_env)
        declared_id = str(clean_env.get("env_fingerprint_id") or "")
        if declared_id and declared_id != computed_id:
            raise ProfilerUsageError(
                f"bench_env_fingerprint_id_mismatch: declared={declared_id!r} computed={computed_id!r}"
            )
        env_id = computed_id
        clean_env["env_fingerprint_id"] = env_id
        bdir = self.bucket_dir(env_id)
        with exclusive_lock(self._bucket_lock(env_id), blocking=True):
            (bdir / "runs").mkdir(parents=True, exist_ok=True)
            env_path = bdir / "env_fingerprint.json"
            if not env_path.exists():
                _atomic_write_json(env_path, clean_env)
            index_path = bdir / "index.json"
            if not index_path.exists():
                index_payload = {
                    "schema": BUCKET_INDEX_SCHEMA,
                    "env_fingerprint_id": env_id,
                    "baseline_clock_mhz": self._qualified_baseline_clock(clean_env, nominal_clock_mhz),
                    "nominal_clock_mhz": float(nominal_clock_mhz) if nominal_clock_mhz is not None else None,
                    "run_shards": [],
                    "entries": {},
                }
                _atomic_write_json(index_path, index_payload)
        self._register_bucket(env_id, clean_env)
        return clean_env

    def _register_bucket(self, env_id: str, env_receipt: Mapping[str, Any]) -> None:
        index_path = self.root / "campaign_index.json"
        with exclusive_lock(self._campaign_lock(), blocking=True):
            if index_path.exists():
                try:
                    catalog = json.loads(index_path.read_text(encoding="utf-8"))
                except TimeoutError:
                    raise
                except (OSError, ValueError):
                    catalog = {}
            else:
                catalog = {}
            buckets = dict(catalog.get("buckets") or {}) if isinstance(catalog, Mapping) else {}
            buckets[env_id] = {
                "env_fingerprint_id": env_id,
                "sku": env_receipt.get("sku"),
                "soc_arch": env_receipt.get("soc_arch"),
                "cann_version": env_receipt.get("cann_version"),
                "va_commit": env_receipt.get("va_commit"),
                "driver_version": env_receipt.get("driver_version"),
                "cache_partition": env_receipt.get("cache_partition"),
                "bucket_relpath": f"buckets/{env_id}",
            }
            _atomic_write_json(
                index_path,
                {"schema": CAMPAIGN_INDEX_SCHEMA, "buckets": buckets},
            )

    def load_index(self, env_fingerprint_id: str) -> dict[str, Any]:
        """Load one bucket's ``index.json`` (returning empty skeleton if uninitialized)."""
        index_path = self.bucket_dir(env_fingerprint_id) / "index.json"
        if not index_path.exists():
            return {
                "schema": BUCKET_INDEX_SCHEMA,
                "env_fingerprint_id": env_fingerprint_id,
                "baseline_clock_mhz": None,
                "nominal_clock_mhz": None,
                "run_shards": [],
                "entries": {},
            }
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except TimeoutError:
            raise
        except (OSError, ValueError) as exc:
            raise ProfilerUsageError(f"bench_bucket_index_corrupt: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise ProfilerUsageError("bench_bucket_index_corrupt: expected object")
        return dict(payload)

    def load_env(self, env_fingerprint_id: str) -> dict[str, Any]:
        """Load one bucket's immutable ``env_fingerprint.json``."""
        env_path = self.bucket_dir(env_fingerprint_id) / "env_fingerprint.json"
        if not env_path.is_file():
            raise ProfilerUsageError(f"bench_bucket_not_found: {env_fingerprint_id}")
        try:
            return dict(json.loads(env_path.read_text(encoding="utf-8")))
        except TimeoutError:
            raise
        except (OSError, ValueError) as exc:
            raise ProfilerUsageError(f"bench_env_receipt_corrupt: {exc}") from exc

    def list_buckets(self) -> list[str]:
        """Return sorted existing ``env_fingerprint_id`` directory names."""
        if not self.buckets_dir.is_dir():
            return []
        return sorted(
            item.name
            for item in self.buckets_dir.iterdir()
            if item.is_dir() and (item / "env_fingerprint.json").is_file()
        )

    def lookup(
        self,
        env_fingerprint_id: str,
        canonical_digest: str,
        capture_mode: str,
        residency: str,
        *,
        boundary: str = "device_kernel",
        split: str | None = None,
        retry_unsupported: bool = False,
        nominal_clock_mhz: float | None = None,
        baseline_clock_mhz: float | None = None,
        index_snapshot: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return a lineage-preserving copy of a reusable cached entry, or ``None``."""
        index = dict(index_snapshot) if index_snapshot is not None else self.load_index(env_fingerprint_id)
        entries = index.get("entries")
        if not isinstance(entries, Mapping):
            return None
        key = index_entry_key(canonical_digest, capture_mode, residency, boundary)
        entry = entries.get(key)
        if not isinstance(entry, Mapping):
            return None
        if str(entry.get("boundary") or "device_kernel") != str(boundary):
            return None
        status = str(entry.get("status") or "")
        if split == "abi_rejection":
            if not retry_unsupported and status == "abi_rejected":
                hit = dict(entry)
                hit["cache_status"] = "hit"
                return hit
            return None
        if status == "ok" and entry.get("qualified") is True:
            nom = nominal_clock_mhz if nominal_clock_mhz is not None else index.get("nominal_clock_mhz")
            base = baseline_clock_mhz if baseline_clock_mhz is not None else index.get("baseline_clock_mhz")
            ok_clock, _reason = validate_clock_band(
                entry.get("observed_clock_mhz"),
                nominal_clock_mhz=nom,
                baseline_clock_mhz=base,
            )
            if not ok_clock:
                return None
            hit = dict(entry)
            hit["cache_status"] = "hit"
            return hit
        if not retry_unsupported and status in {"abi_rejected", "abi_unsupported"}:
            hit = dict(entry)
            hit["cache_status"] = "hit"
            return hit
        return None

    def commit_run(
        self,
        env_fingerprint: Mapping[str, Any],
        *,
        run_id: str,
        observation_rows: Sequence[Mapping[str, Any]],
        case_entries: Sequence[Mapping[str, Any]],
        nominal_clock_mhz: float | None = None,
        home: str | None = None,
    ) -> dict[str, Any]:
        """Write an immutable per-run shard ``runs/<run_id>.jsonl`` and update ``index.json`` atomically."""
        clean_env = self.ensure_bucket(env_fingerprint, nominal_clock_mhz=nominal_clock_mhz, home=home)
        env_id = str(clean_env["env_fingerprint_id"])
        bdir = self.bucket_dir(env_id)
        shard_rel = f"runs/{run_id}.jsonl"
        shard_path = bdir / shard_rel
        with exclusive_lock(self._bucket_lock(env_id), blocking=True):
            index = self.load_index(env_id)
            shards = list(index.get("run_shards") or [])
            committed_ids = {str(s.get("run_id") or "") for s in shards if isinstance(s, Mapping)}
            if str(run_id) in committed_ids:
                raise ProfilerUsageError(f"bench_run_shard_already_exists: {shard_rel}")
            shard_lines: list[str] = []
            for row in observation_rows:
                clean_row = portable_receipt(row, home=home)
                shard_lines.append(
                    json.dumps(clean_row, ensure_ascii=False, sort_keys=True) + "\n"
                )
            tmp_shard = shard_path.with_name(f".{shard_path.name}.tmp.{os.getpid()}")
            data = "".join(shard_lines).encode("utf-8")
            fd = os.open(tmp_shard, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _JOURNAL_MODE)
            try:
                if data and os.write(fd, data) != len(data):
                    raise OSError("short run shard write")
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(tmp_shard, shard_path)
            ObservationJournal(shard_path).repair()
            shard_sha = _file_sha256(shard_path)

            entries = dict(index.get("entries") or {})
            shards.append({
                "run_id": str(run_id),
                "path": shard_rel,
                "observations_sha256": shard_sha,
                "record_count": len(shard_lines),
            })
            if index.get("nominal_clock_mhz") is None and nominal_clock_mhz is not None:
                index["nominal_clock_mhz"] = float(nominal_clock_mhz)
            eff_nom = index.get("nominal_clock_mhz")
            if index.get("baseline_clock_mhz") is None:
                index["baseline_clock_mhz"] = self._qualified_baseline_clock(clean_env, eff_nom)

            for item in case_entries:
                clean_item = portable_receipt(item, home=home)
                digest = str(clean_item.get("canonical_key_digest") or "")
                mode = str(clean_item.get("capture_mode") or "eager")
                res = str(clean_item.get("residency") or "cold_hbm")
                boundary = str(clean_item.get("boundary") or "device_kernel")
                if not digest:
                    continue
                ekey = index_entry_key(digest, mode, res, boundary)
                existing = entries.get(ekey)
                if isinstance(existing, Mapping):
                    existing_qualified = existing.get("status") == "ok" and existing.get("qualified") is True
                    incoming_qualified = clean_item.get("status") == "ok" and clean_item.get("qualified") is True
                    if existing_qualified and not incoming_qualified:
                        # Never-Overwrite-Qualified invariant
                        continue
                stored = dict(clean_item)
                had_shard = bool(stored.get("run_shard"))
                stored.setdefault("run_shard", shard_rel)
                if not stored.get("raw_sha256") or not had_shard or not verify_case_raw_sha256(stored):
                    stored = seal_case_raw_sha256(stored)
                entries[ekey] = stored

            index["run_shards"] = shards
            index["entries"] = entries
            _atomic_write_json(bdir / "index.json", index)
            return {
                "env_fingerprint_id": env_id,
                "run_id": str(run_id),
                "shard_relpath": shard_rel,
                "shard_path": str(shard_path),
                "observations_sha256": shard_sha,
                "record_count": len(shard_lines),
                "run_shards": shards,
            }


__all__ = [
    "BUCKET_INDEX_SCHEMA",
    "CAMPAIGN_INDEX_SCHEMA",
    "CAMPAIGN_SCHEMA",
    "CANONICAL_KEY_FIELDS",
    "CASE_RAW_SHA256_EXCLUDED_FIELDS",
    "CampaignStore",
    "PLAN_V2_SCHEMA",
    "canonical_case_id",
    "canonical_json",
    "canonical_key_digest",
    "index_entry_key",
    "load_training_manifest_freeze",
    "normalize_canonical_key",
    "seal_case_raw_sha256",
    "seal_payload",
    "sha256_canonical",
    "stream_shards_sha256",
    "synthesize_canonical_key_from_v1_case",
    "verify_case_canonical_key",
    "verify_case_raw_sha256",
    "verify_seal",
]
