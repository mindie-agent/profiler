"""Source-declared sim Case materialization for the A5 multinode/rack fleet rows.

Joins each capture row to its original campaign/rack launch files, the on-disk
model config and quantization description, and same-host hardware evidence; then
composes a validated sim ``Case`` with no measured timing or service regimes.
``resolve_campaign_case(row)`` returns a probe-shaped mapping or ``None`` outside
the two owned suites.  Undeclared rows return ``ok=False`` with exact needs.
"""
from __future__ import annotations
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence
CAMPAIGN_SUITE = "a5_multinode_full_coverage_20261108"
RACK_SUITE = "a5_rack06_rack08_multirank_20261107"
CAMPAIGN_PREFIX = "a5_multinode_20261108:"
CAMPAIGN_ROOT = Path("/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108")
GLM51_SOURCE_CASE = Path(__file__).with_name("cases") / "decode-a5_glm51_mxfp4_dp16tp1ep16_pf1k.json"
WEIGHTS_CATALOG = Path("/Volumes/data/mindie-sim-data/a5/weights-catalog")
WORKSTREAM_ROOTS = (
    Path("/Volumes/data/mindie-agent-workstreams"),
    Path("/Users/maoxx241/code/mindie-agent/.workstreams"),
)
_RANK_RE = re.compile(r"^dp(\d+)_pp(\d+)_tp(\d+)_dcp(\d+)_ep(\d+)_rank(\d+)")
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None
def glm51_source_case(*, model_label: Any, model_case: Any) -> Path | None:
    """Select the retained GLM-5.1 R64 catalogue case when a cell still names the GLM-5.3 template."""
    label = str(model_label or "").lower()
    if "glm-5.1" not in label and "glm51" not in label:
        return None
    if model_case is not None:
        raw = _read_json(Path(model_case)); model = raw.get("model") if raw else None
        name = str((model or {}).get("name") or (model or {}).get("catalog_key") or "").lower()
        if "glm-5.1" in name or "glm51" in name:
            return None
    return GLM51_SOURCE_CASE if GLM51_SOURCE_CASE.is_file() else None
def _read_json_any(path: Path) -> Any:
    try:
        return json.load(path.open(encoding="utf-8"))
    except (OSError, ValueError):
        return None
def _int(value: Any) -> int | None:
    try:
        return None if isinstance(value, bool) or value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None
def clear_caches() -> None:
    _declared_device_memory.cache_clear()
    _hardware_index.cache_clear()
    _model_config.cache_clear()
    _sku_profiles.cache_clear()
def configure_sources(*, campaign_root: Path | None = None, weights_catalog: Path | None = None,
                      workstream_roots: Sequence[Path] | None = None) -> None:
    """Retarget source roots (tests only); clears derived caches."""
    global CAMPAIGN_ROOT, WEIGHTS_CATALOG, WORKSTREAM_ROOTS
    if campaign_root is not None:
        CAMPAIGN_ROOT = Path(campaign_root)
    if weights_catalog is not None:
        WEIGHTS_CATALOG = Path(weights_catalog)
    if workstream_roots is not None:
        WORKSTREAM_ROOTS = tuple(Path(item) for item in workstream_roots)
    clear_caches()
@lru_cache(maxsize=1)
def _sku_profiles() -> dict[str, dict[str, Any]]:
    # Read the registered hardware catalog file directly.  The live compose
    # registry gains runtime alias entries after a synthesis; that mutable
    # state is not part of the declared SKU catalog.
    catalog = Path(__file__).resolve().parents[3] / "sim" / "mindie_sim" / "backends" / "profiles" / "ascend.json"
    raw = _read_json(catalog)
    return {str(key): dict(value) for key, value in (raw or {}).items() if isinstance(value, Mapping)}
def _npu_facts(npu_raw: str) -> tuple[str | None, int | None, int]:
    """Return (device_name, hbm_mib, npu_count) parsed from ``npu-smi info`` text."""
    names: list[str] = []
    hbm: list[int] = []
    for line in npu_raw.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].isdigit() and cells[1].startswith("Ascend"):
            names.append(cells[1])
        for cell in cells:
            match = re.search(r"(\d+)\s*/\s*(\d+)\s*$", cell)
            if match:
                hbm.append(int(match.group(2)))
    unique = sorted(set(names)); return (unique[0] if len(unique) == 1 else None, max(hbm) if hbm else None, len(names))
@lru_cache(maxsize=1)
def _hardware_index() -> dict[str, Any]:
    """Node -> declared device facts from same-host preflight evidence."""
    nodes: dict[str, dict[str, Any]] = {}
    for root in WORKSTREAM_ROOTS:
        if not root.is_dir():
            continue
        for workstream in sorted(root.glob("a5-*/")):
            for path in sorted((workstream / "evidence").glob("preflight*.json")):
                raw = _read_json_any(path)
                for item in (raw if isinstance(raw, list) else [raw]):
                    if not isinstance(item, Mapping) or not item.get("node") or not item.get("npu_raw"):
                        continue
                    name, hbm, count = _npu_facts(str(item["npu_raw"]))
                    entry = nodes.setdefault(str(item["node"]), {"device_name": None, "hbm_mib": None,
                                                                 "npu_count": None, "evidence": []})
                    entry["device_name"] = name or entry["device_name"]
                    entry["hbm_mib"] = hbm or entry["hbm_mib"]
                    entry["npu_count"] = count or entry["npu_count"]
                    entry["evidence"].append({"path": str(path), "sha256": _sha256(path)})
            inventory = _read_json(workstream / "evidence" / "fleet_inventory.json")
            for item in (inventory or {}).get("nodes") or ():
                if not isinstance(item, Mapping) or not item.get("node"):
                    continue
                entry = nodes.setdefault(str(item["node"]), {"device_name": None, "hbm_mib": None,
                                                             "npu_count": None, "evidence": []})
                entry["npu_count"] = _int(item.get("npu_count")) or entry["npu_count"]
                entry["evidence"].append({"path": str(workstream / "evidence" / "fleet_inventory.json"),
                                          "sha256": _sha256(workstream / "evidence" / "fleet_inventory.json")})
    return {"nodes": nodes}

def _resolve_hardware(nodes: Sequence[str], memory_hint_mib: int | None = None) -> dict[str, Any] | None:
    index = _hardware_index()
    facts: list[tuple[str, int | None, int | None, list[dict[str, str]]]] = []
    for node in nodes:
        entry = index["nodes"].get(str(node))
        if entry is None:
            return None
        facts.append((entry.get("device_name") or "", entry.get("hbm_mib"),
                      entry.get("npu_count"), list(entry.get("evidence") or ())))
    names = {item[0] for item in facts if item[0]}
    counts = {item[2] for item in facts if item[2]}
    hbms = {item[1] for item in facts if item[1]}
    if len(counts) != 1:
        return None
    ranks = counts.pop()
    if int(ranks) != 8:
        return None
    profiles = _sku_profiles()
    candidates: list[str] = []
    has_host_facts = len(names) == 1 and len(hbms) == 1
    device_name: str | None = None
    hbm_mib: int | None = None
    if has_host_facts:
        device_name, hbm_mib = names.pop(), hbms.pop()
        for key, profile in profiles.items():
            device = profile.get("device") if isinstance(profile.get("device"), Mapping) else {}
            if profile.get("architecture") != "A5":
                continue
            if device_name.startswith("Ascend950") and key == device_name:
                candidates.append(key)
                continue
            if hbm_mib is not None and int(device.get("memory_bytes") or 0) == int(hbm_mib) * 1024 * 1024:
                candidates.append(key)
    elif memory_hint_mib is not None:
        # The run's own host log reports the total device memory visible to
        # vLLM (e.g. 91.75 GiB on a 96 GiB part).  Match the registered SKU
        # capacity that contains it within the firmware/driver reserve band.
        for key, profile in profiles.items():
            device = profile.get("device") if isinstance(profile.get("device"), Mapping) else {}
            capacity = int(device.get("memory_bytes") or 0) // (1024 * 1024)
            if profile.get("architecture") != "A5":
                continue
            if int(memory_hint_mib) <= capacity <= int(memory_hint_mib) + 8 * 1024:
                candidates.append(key)
    evidence, seen = [], set()
    for item in [entry_evidence for entry in facts for entry_evidence in entry[3]]:
        key = (item.get("path"), item.get("sha256"))
        if key not in seen:
            seen.add(key)
            evidence.append(item)
    chosen = profiles[candidates[0]] if len(candidates) == 1 else {}
    capacity_mib = int((chosen.get("device") or {}).get("memory_bytes") or 0) // (1024 * 1024)
    unique = len(candidates) == 1
    return {"sku": candidates[0] if unique else None, "candidates": candidates, "ranks_per_node": int(ranks),
            "topology_preset": "a5_server", "hbm_mib": capacity_mib or None,
            "device_name": (device_name if has_host_facts else candidates[0]) if unique else None,
            "reported_device_memory_mib": hbm_mib if has_host_facts else int(memory_hint_mib or 0) or None,
            "identity_basis": "same_node_npu_smi" if has_host_facts else "declared_run_device_memory",
            "evidence": evidence}
def _quant_family(token: str) -> str:
    text = str(token).upper()
    if "W4A8" in text: return "w4a8"
    if "W4A4" in text: return "mxfp4"
    if "MXFP8" in text or text.startswith("FP8"): return "mxfp8"
    if "MXFP4" in text: return "mxfp4"
    return "w8a8" if "W8A8" in text else "unknown"
def _quant_format(family: str) -> dict[str, Any]:
    table = {
        "mxfp8": ("fp8_e4m3", "fp8_e4m3", (1, 32), 32, "fp8_e8m0", 1.0, 32, "fp8_e8m0", 2),
        "mxfp4": ("mxfp4", "fp8_e4m3", (1, 32), 32, "fp8_e8m0", 1.0, 0, "", 1),
        "w4a8": ("int8", "int8", (1, 1), 1, "fp32", 4.0, 0, "", 1),
        "w8a8": ("int8", "int8", (1, 1), 1, "fp32", 4.0, 0, "", 1),
    }
    weight, activation, block, expert_block, scale, scale_bytes, group, scale_fmt, pack = table.get(
        family, ("bf16", "bf16", (0, 0), 32, "fp32", 4.0, 0, "", 1))
    return {"weight_format": weight, "activation_format": activation, "block": block,
            "expert_block": expert_block, "scale_format": scale, "scale_bytes": scale_bytes,
            "activation_group_size": group, "activation_scale_format": scale_fmt, "activation_scale_pack": pack}
def _quant_spec_mapping(weight_family: str, expert_family: str,
                        overrides: Mapping[str, str] | None = None,
                        kv_dtype: str = "") -> dict[str, Any]:
    weight, expert = _quant_format(weight_family), _quant_format(expert_family)
    kv = _normalize_kv_dtype(kv_dtype) or "bf16"
    return {
        "name": f"declared_split_{weight_family}_{expert_family}",
        "weight_format": weight["weight_format"], "activation_format": weight["activation_format"],
        "expert_weight_format": "int4" if expert_family == "w4a8" else expert["weight_format"],
        "weight_block": list(weight["block"]), "expert_block": expert["expert_block"],
        "scale_format": weight["scale_format"], "scale_bytes": weight["scale_bytes"],
        "kv_dtype": kv, "index_dtype": "bf16", "index_scale_dtype": "none", "native_format": "bf16",
        "exclusions": ["mtp", "norm", "lm_head", "embedding", "vision", "projector",
                       "conv_weight_f32", "conv_weight_bf16"],
        "activation_group_size": weight["activation_group_size"],
        "activation_scale_format": weight["activation_scale_format"],
        "activation_scale_pack": weight["activation_scale_pack"],
        "category_overrides": [[category,
                                [["weight_format", family],
                                 ["activation_format", _quant_format(family)["activation_format"]]]]
                               for category, family in sorted((overrides or {}).items())],
    }
@lru_cache(maxsize=512)
def _model_config(model_path: str) -> dict[str, Any] | None:
    name = Path(str(model_path).replace("\\", "/")).name
    directory = WEIGHTS_CATALOG / name
    config = directory / "config.json"
    if not config.is_file():
        return None
    result: dict[str, Any] = {"name": name, "directory": str(directory), "config_path": str(config),
                              "config_sha256": _sha256(config), "quant": None, "quant_source": None}
    description = directory / "quant_model_description.json"
    if description.is_file():
        raw = _read_json(description)
        classes: dict[str, int] = {}
        expert_classes: dict[str, int] = {}
        non_expert_keys: dict[str, list[str]] = {}
        for key, value in (raw or {}).items():
            text = str(key)
            if not text.endswith(".weight") or not isinstance(value, str):
                continue
            if any(token in text for token in ("vision", "audio", "projector", "multi_modal")):
                continue
            token = value.upper()
            if token in {"FLOAT", "BF16", "NONE"}:
                continue
            family = _quant_family(token)
            classes[family] = classes.get(family, 0) + 1
            if ".experts." in text or "mlp.experts" in text:
                expert_classes[family] = expert_classes.get(family, 0) + 1
            else:
                non_expert_keys.setdefault(family, []).append(text)
        total = sum(classes.values())
        result["weight_classes"] = dict(sorted(classes.items()))
        result["expert_weight_classes"] = dict(sorted(expert_classes.items()))
        result["quant_represented"] = False
        if total and "unknown" not in classes:
            dominant, count = max(classes.items(), key=lambda item: item[1])
            non_expert = {family: len(keys) for family, keys in non_expert_keys.items()}
            weight_family = max(non_expert, key=non_expert.get) if non_expert else None
            expert_family = (max(expert_classes, key=expert_classes.get)
                             if expert_classes else weight_family)
            overrides: dict[str, str] = {}
            if weight_family is not None:
                for family, keys in non_expert_keys.items():
                    if family == weight_family:
                        continue
                    if all(".shared_expert" in key for key in keys):
                        overrides["shared_expert"] = family
                    elif all(".mlp." in key for key in keys):
                        overrides["dense_mlp"] = family
                    else:
                        overrides = {}
                        break
            if len(classes) == 1:
                result["quant"] = dominant
                result["quant_representation"] = f"single_format:{dominant}"
                result["quant_represented"] = True
                result["quant_source"] = {
                    "path": str(description), "sha256": _sha256(description),
                    "dominant_weight_tensors": count, "classified_weight_tensors": total,
                }
            elif weight_family is not None and expert_family is not None and (
                    weight_family != expert_family or overrides) and (
                    expert_classes or overrides):
                result["quant"] = weight_family
                result["quant_weight_family"] = weight_family
                result["quant_expert_family"] = expert_family
                result["quant_overrides"] = dict(overrides)
                result["quant_spec"] = _quant_spec_mapping(
                    weight_family, expert_family, overrides,
                    str(result.get("kv_cache_dtype") or ""))
                result["quant_represented"] = True
                result["quant_representation"] = (
                    f"split:weight={weight_family}:expert={expert_family}:"
                    f"overrides={','.join(f'{k}={v}' for k, v in sorted(overrides.items())) or 'none'}")
                result["quant_source"] = {
                    "path": str(description), "sha256": _sha256(description),
                    "weight_classes": dict(sorted(classes.items())),
                    "expert_weight_classes": dict(sorted(expert_classes.items())),
                }
            else:
                result["quant"] = dominant
                result["quant_representation"] = "dominant_substitution"
                result["quant_source"] = {
                    "path": str(description), "sha256": _sha256(description),
                    "dominant_weight_tensors": count, "classified_weight_tensors": total,
                }
    return result
def _scope(row: Mapping[str, Any]) -> dict[str, Any] | None:
    capture_id = str(row.get("capture_id") or "")
    suite = str(row.get("suite") or "")
    if capture_id.startswith(CAMPAIGN_PREFIX) or suite == CAMPAIGN_SUITE:
        body = capture_id[len(CAMPAIGN_PREFIX):] if capture_id.startswith(CAMPAIGN_PREFIX) else capture_id
        parts = body.split(":")
        if len(parts) == 2 or (len(parts) == 3 and parts[2] == "idle_dp_rank"):
            return {"kind": "campaign", "case": parts[0], "cell": parts[1], "idle": len(parts) == 3}
        return None
    marker = "a5-multinode-fleet-rack0"
    if marker in capture_id or suite == RACK_SUITE:
        parts = (capture_id[capture_id.index(marker):] if marker in capture_id else capture_id).split("/")
        out = parts.index("out") if "out" in parts else -4
        return ({"kind": "rack", "workstream": parts[0], "case": parts[out + 1],
                 "cell": parts[out + 2], "node": parts[out + 3], "profile_dir": parts[-1]}
                if len(parts) >= out + 4 else None)
    return None
@lru_cache(maxsize=256)
def _declared_device_memory(run_dir: Path) -> dict[str, Any] | None:
    """Reported NPU total memory from this run's own vLLM startup log."""
    totals: dict[float, Path] = {}
    for path in sorted(run_dir.glob("vllm_rank*.log")):
        try:
            with path.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    match = re.search(r"Free memory on device \([0-9.]+/([0-9.]+) GiB\)", line)
                    if match:
                        totals.setdefault(float(match.group(1)), path)
        except OSError:
            continue
    if not totals:
        return None
    values = sorted(totals)
    if values[-1] - values[0] > 0.05:
        return None
    return {"total_mib": int(round(values[0] * 1024)), "path": str(totals[values[0]]), "sha256": _sha256(totals[values[0]])}
def _normalize_kv_dtype(value: Any) -> str | None:
    return {"fp8": "fp8_e4m3", "fp8_e4m3": "fp8_e4m3", "fp8_e5m2": "fp8_e5m2",
            "bf16": "bf16", "bfloat16": "bf16", "fp16": "fp16"}.get(str(value or "").lower())
def _graph_mode(mode: str, phase: str, eager: bool) -> str:
    """Translate the declared vLLM graph mode without inventing a capture."""
    if eager:
        return "none"
    token = str(mode or "").strip().upper()
    if token in {"PIECEWISE", "PIECEWISE_CAPTURE"}:
        return "piecewise"
    return "full" if token in {"FULL", "FULL_AND_PIECEWISE", "FULL_DECODE_ONLY"} and phase == "decode" else "none"
def _failure(diagnostics: Sequence[str], needed: Sequence[str],
             source: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"ok": False, "status": "insufficient_evidence", "diagnostics": list(diagnostics), "needed": list(needed), "source": dict(source or {}), "case": None}
def _campaign_declaration(scope: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    run_dir = CAMPAIGN_ROOT / "runs" / str(scope["case"])
    spec_path, manifest_path = run_dir / "case_spec.json", run_dir / "manifest.json"
    spec, manifest = _read_json(spec_path), _read_json(manifest_path)
    if spec is None or manifest is None:
        return _failure(["campaign_case_spec_or_manifest_missing"],
                        ["runs/<case>/case_spec.json", "runs/<case>/manifest.json"])
    cell = str(scope["cell"])
    cell_path = run_dir / f"{cell}.json"
    cell_meta = _read_json(cell_path) if cell_path.is_file() else {}
    if not cell_meta:
        for item in spec.get("cells") or ():
            if isinstance(item, Mapping) and str(item.get("tag")) == cell:
                cell_meta = dict(item)
                break
    if not cell_meta:
        return _failure([f"missing_cell_launch_declaration:{cell}"],
                        ["runs/<case>/<cell>.json or case_spec.cells[tag]"])
    mode = str(cell_meta.get("mode") or "")
    isl, osl = _int(cell_meta.get("isl")), _int(cell_meta.get("osl"))
    concurrency = _int(cell_meta.get("concurrency"))
    if not mode or not isl or not osl or not concurrency:
        return _failure([f"cell_workload_incomplete:{cell}"],
                        ["mode", "isl", "osl", "concurrency"])
    tp, dp = _int(manifest.get("tp")), _int(manifest.get("dp"))
    spec_tp, spec_dp = _int(spec.get("tp")), _int(spec.get("dp"))
    if tp is not None and spec_tp is not None and tp != spec_tp:
        return _failure([f"parallel_conflict:tp:manifest={tp}:case_spec={spec_tp}"], [])
    if dp is not None and spec_dp is not None and dp != spec_dp:
        return _failure([f"parallel_conflict:dp:manifest={dp}:case_spec={spec_dp}"], [])
    tp, dp = tp or spec_tp, dp or spec_dp
    if not tp or not dp:
        return _failure(["parallel_not_declared"], ["tp", "dp"])
    ep = tp * dp if spec.get("enable_expert_parallel") is True else 1
    nodes = manifest.get("nodes") or spec.get("nodes") or ()
    if not isinstance(nodes, (list, tuple)) or not nodes:
        return _failure(["nodes_not_declared"], ["nodes"])
    model_path = manifest.get("model_path") or spec.get("model_path")
    if not model_path:
        return _failure(["model_path_not_declared"], ["model_path"])
    prefix = float(cell_meta.get("prefix_cache_ratio") or 0.0)
    mixed = mode == "mixed_multiturn"
    phase = "prefill" if mode == "prefill_only" else "decode"
    compilation = spec.get("compilation_config") if isinstance(spec.get("compilation_config"), Mapping) else {}
    speculative = spec.get("speculative_config") if isinstance(spec.get("speculative_config"), Mapping) else {}
    additional = spec.get("additional_config") if isinstance(spec.get("additional_config"), Mapping) else {}
    attention = spec.get("attention_config") if isinstance(spec.get("attention_config"), Mapping) else {}
    eager = speculative.get("enforce_eager") is True or spec.get("enforce_eager") is True
    mtp = _int(speculative.get("num_speculative_tokens")) or 0
    sizes = sorted({int(item) for item in compilation.get("cudagraph_capture_sizes") or ()
                    if _int(item) and int(item) > 0})
    prefix_caching = spec.get("enable_prefix_caching")
    prefix_tokens = 0 if prefix_caching is False else int(round(isl * prefix))
    declaration = {
        "kind": "campaign", "phase": phase,
        "graph_mode": _graph_mode(str(compilation.get("cudagraph_mode") or "none"), phase, eager),
        "graph_capture_sizes": sizes if phase == "decode" else [],
        "mtp_proposal_tokens": mtp,
        "speculative_method": str(speculative.get("method") or "") or None,
        "enforce_eager": eager,
        "rank_export": "idle_dp_rank" if scope.get("idle") else "primary",
        "population_basis": ("mixed_multiturn_decode_tpot" if mixed else "declared_single_phase"),
        "mode": mode, "tp": tp, "dp": dp, "ep": ep, "pp": 1,
        "nodes": [str(node) for node in nodes], "model_path": str(model_path),
        "prompt_tokens": isl, "output_tokens": osl, "concurrency": concurrency,
        "prefix_tokens": prefix_tokens,
        "prefix_cache_basis": ("disabled_by_source" if prefix_caching is False
                               else "declared_prefix_cache_ratio"),
        "max_num_seqs": _int(spec.get("max_num_seqs")),
        "max_num_batched_tokens": _int(spec.get("max_num_batched_tokens")),
        "max_model_len": _int(spec.get("max_model_len")),
        "block_size": _int(spec.get("block_size")) or _int(spec.get("kv_block_size")),
        "gpu_memory_utilization": spec.get("gpu_memory_utilization"),
        "enable_chunked_prefill": spec.get("enable_chunked_prefill"),
        "kv_cache_dtype": spec.get("kv_cache_dtype"),
        "attention_config": dict(attention),
        "indexer_kv_dtype": attention.get("indexer_kv_dtype"),
        "enable_prefix_caching": prefix_caching,
        "additional_config": dict(additional),
        "enable_shared_expert_dp": additional.get("enable_shared_expert_dp") is True,
        "multistream_overlap_shared_expert": additional.get("multistream_overlap_shared_expert") is True,
        "chunked_prefill_source": ("case_spec" if "enable_chunked_prefill" in spec
                                   else "undeclared_compose_default"),
        "source": {
            "case_spec": {"path": str(spec_path), "sha256": _sha256(spec_path)},
            "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
            "cell_launch": ({"path": str(cell_path), "sha256": _sha256(cell_path)}
                            if cell_path.is_file() else {"path": str(spec_path), "sha256": _sha256(spec_path),
                                                         "boundary": "case_spec.cells[tag]"}),
            "model_path": str(model_path),
            "image": str(spec.get("image") or ""),
        },
    }
    memory = _declared_device_memory(run_dir)
    if memory is not None:
        declaration["device_memory_mib"] = memory["total_mib"]
        declaration["source"]["device_memory"] = memory
    export_dir = run_dir / cell / ("idle_dp_rank" if scope.get("idle") else "")
    for profiler in sorted(export_dir.glob("profiler_info_*.json")):
        info = _read_json(profiler)
        if info is not None and _int(info.get("rank_id")) is not None:
            rank_id = _int(info["rank_id"])
            declaration["source"]["export_rank"] = {
                "rank_id": rank_id, "path": str(profiler), "sha256": _sha256(profiler),
                "rank_observed": True, "batch_observed": False}
            if tp > 0 and 0 <= rank_id // tp < dp:
                declaration["source"]["physical_rank"] = {
                    "rank_id": rank_id, "dp_index": rank_id // tp, "tp_index": rank_id % tp,
                    "rank_observed": True, "role": str(declaration.get("rank_export") or "primary")}
            break
    if not scope.get("idle"):
        declaration["source"]["active_rank"] = dict(declaration["source"].get("physical_rank") or {})
        for profiler in sorted((run_dir / cell / "idle_dp_rank").glob("profiler_info_*.json")):
            info = _read_json(profiler)
            if info is not None and _int(info.get("rank_id")) is not None:
                rank_id = _int(info["rank_id"])
                if tp > 0 and 0 <= rank_id // tp < dp:
                    declaration["source"]["idle_rank"] = {
                        "rank_id": rank_id, "dp_index": rank_id // tp, "tp_index": rank_id % tp,
                        "path": str(profiler), "sha256": _sha256(profiler),
                        "rank_observed": True, "batch_observed": False}
                break
    else:
        for profiler in sorted((run_dir / cell).glob("profiler_info_*.json")):
            info = _read_json(profiler)
            if info is not None and _int(info.get("rank_id")) is not None:
                rank_id = _int(info["rank_id"])
                if tp > 0 and 0 <= rank_id // tp < dp:
                    declaration["source"]["active_rank"] = {
                        "rank_id": rank_id, "dp_index": rank_id // tp, "tp_index": rank_id % tp,
                        "path": str(profiler), "sha256": _sha256(profiler),
                        "rank_observed": True, "batch_observed": False}
                break
    return declaration
def _parse_cmd(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    result: dict[str, Any] = {}
    for key, pattern in (
        ("prompt_tokens", r"--prompt-tokens\s+(\d+)"),
        ("output_tokens", r"--max-tokens\s+(\d+)"),
        ("concurrency", r"--concurrency\s+(\d+)"),
        ("prefix_tokens", r"--shared-tokens\s+(\d+)"),
        ("block_size", r"--block-size\s+(\d+)"),
        ("mode", r"--mode\s+([A-Za-z0-9_]+)"),
    ):
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1)
    return result
def _rack_declaration(scope: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    root = next((base / str(scope["workstream"]) for base in WORKSTREAM_ROOTS
                 if (base / str(scope["workstream"])).is_dir()), None)
    if root is None:
        return _failure([f"workstream_root_missing:{scope['workstream']}"], [])
    declaration_path = root / "cases" / f"{scope['case']}.json"
    spec = _read_json(declaration_path)
    if spec is None:
        blocked = root / "cases" / f"{scope['case']}.BLOCKED.md"
        return _failure(["cohort_declaration_missing" if not blocked else "cohort_blocked_in_source"],
                        [str(declaration_path)])
    cell_dir = root / "out" / str(scope["case"]) / str(scope["cell"])
    cmd_path = cell_dir / "cmd.sh"
    cmd = _parse_cmd(cmd_path) if cmd_path.is_file() else {}
    if not cmd or not cmd.get("prompt_tokens") or not cmd.get("output_tokens") or not cmd.get("concurrency"):
        return _failure([f"missing_cell_launcher:{scope['cell']}"], [str(cmd_path)])
    tp, dp = _int(spec.get("tp")), _int(spec.get("dp"))
    if not tp or not dp:
        return _failure(["parallel_not_declared"], ["tp", "dp"])
    ep = tp * dp if spec.get("enable_expert_parallel") is True else 1
    nodes = spec.get("nodes") or ()
    if not isinstance(nodes, (list, tuple)) or not nodes:
        return _failure(["nodes_not_declared"], ["nodes"])
    mode = str(cmd.get("mode") or "")
    phase = "prefill" if "prefill" in mode else "decode"
    model_path = spec.get("model")
    if not model_path:
        return _failure(["model_path_not_declared"], ["model"])
    compilation = spec.get("compilation_config") if isinstance(spec.get("compilation_config"), Mapping) else {}
    speculative = spec.get("speculative_config") if isinstance(spec.get("speculative_config"), Mapping) else {}
    eager = speculative.get("enforce_eager") is True or spec.get("enforce_eager") is True
    sizes = sorted({int(item) for item in compilation.get("cudagraph_capture_sizes") or ()
                    if _int(item) and int(item) > 0})
    profile_dir = str(scope.get("profile_dir") or "")
    # The public capture id may carry a staging name ("node") where the
    # retained tree has the host name (177.25.23.1).  Bind the exact worker by
    # requiring one directory with the declared worker suffix under the cell.
    matches = sorted(cell_dir.glob(f"*/{profile_dir}")) if profile_dir else []
    if len(matches) != 1:
        return _failure([f"rank_worker_directory_not_unique:{profile_dir}:{len(matches)}"],
                        [str(cell_dir / "<node>" / profile_dir)])
    worker_dir = matches[0]
    rank_match = _RANK_RE.match(profile_dir)
    if rank_match is None:
        return _failure([f"rank_worker_identity_unparsable:{profile_dir}"], [])
    rank = {
        "dp": int(rank_match.group(1)), "pp": int(rank_match.group(2)), "tp": int(rank_match.group(3)),
        "dcp": int(rank_match.group(4)), "ep": int(rank_match.group(5)), "rank": int(rank_match.group(6)),
    }
    if rank["dp"] >= dp or rank["ep"] >= ep or rank["tp"] >= tp or rank["pp"] >= 1:
        return _failure([f"rank_index_out_of_declared_range:{rank}"], [])
    source = {
        "case_declaration": {"path": str(declaration_path), "sha256": _sha256(declaration_path)},
        "cell_launcher": {"path": str(cmd_path), "sha256": _sha256(cmd_path)},
        "model_path": str(model_path),
        "image": str(spec.get("image") or ""),
    }
    source["rank"] = rank
    source["rank_worker"] = {"node": worker_dir.parent.name, "path": str(worker_dir),
                             "rank_observed": True, "batch_observed": False}
    additional = spec.get("additional_config") if isinstance(spec.get("additional_config"), Mapping) else {}
    attention = spec.get("attention_config") if isinstance(spec.get("attention_config"), Mapping) else {}
    prefix_caching = spec.get("enable_prefix_caching")
    prefix_tokens = 0 if prefix_caching is False else int(cmd.get("prefix_tokens") or 0)
    gpu = spec.get("gpu_memory_utilization")
    return {
        "kind": "rack", "phase": phase,
        "graph_mode": _graph_mode(str(compilation.get("cudagraph_mode") or "none"), phase, eager),
        "graph_capture_sizes": sizes if phase == "decode" else [],
        "mtp_proposal_tokens": _int(speculative.get("num_speculative_tokens")) or 0,
        "speculative_method": str(speculative.get("method") or "") or None,
        "enforce_eager": eager,
        "rank_export": "primary",
        "device_memory_mib": None,
        "mode": mode, "tp": tp, "dp": dp, "ep": ep, "pp": 1,
        "nodes": [str(node) for node in nodes], "model_path": str(model_path),
        "prompt_tokens": int(cmd["prompt_tokens"]), "output_tokens": int(cmd["output_tokens"]),
        "concurrency": int(cmd["concurrency"]), "prefix_tokens": prefix_tokens,
        "prefix_cache_basis": ("disabled_by_source" if prefix_caching is False
                               else "declared_launch_shared_tokens"),
        "max_num_seqs": _int(spec.get("max_num_seqs")),
        "max_num_batched_tokens": _int(spec.get("max_num_batched_tokens")),
        "max_model_len": _int(spec.get("max_model_len")),
        "block_size": _int(cmd.get("block_size")) or _int(spec.get("block_size")),
        "gpu_memory_utilization": gpu if gpu is not None else spec.get("gpu_mem"),
        "enable_chunked_prefill": spec.get("enable_chunked_prefill"),
        "kv_cache_dtype": spec.get("kv_cache_dtype"),
        "attention_config": dict(attention),
        "indexer_kv_dtype": attention.get("indexer_kv_dtype"),
        "enable_prefix_caching": prefix_caching,
        "additional_config": dict(additional),
        "enable_shared_expert_dp": additional.get("enable_shared_expert_dp") is True,
        "multistream_overlap_shared_expert": additional.get("multistream_overlap_shared_expert") is True,
        "chunked_prefill_source": ("case_declaration" if "enable_chunked_prefill" in spec
                                   else "undeclared_compose_default"),
        "profile_dir": str(scope.get("profile_dir") or ""),
        "node": str(scope.get("node") or ""),
        "source": source,
    }
def _compose_model_input(model: Mapping[str, Any]) -> tuple[Any, list[str]]:
    """Return the declared model config, translating only real missing aliases."""
    path = Path(str(model["config_path"]))
    raw = _read_json(path)
    if raw is None:
        return model["config_path"], []
    notes: list[str] = []
    normalized = dict(raw)
    text = normalized.get("text_config") if isinstance(normalized.get("text_config"), Mapping) else {}
    if raw.get("num_experts_per_tok") is None and raw.get("top_k") is None:
        top_k = _int(raw.get("top_k_experts") or text.get("top_k_experts"))
        experts = _int(raw.get("n_routed_experts") or raw.get("num_experts")
                       or text.get("n_routed_experts") or text.get("num_experts"))
        if top_k and experts and 0 < top_k <= experts:
            # Gemma4 declares top_k_experts; the registered config alias map does
            # not yet include that spelling.  Carry the declared value through.
            normalized["num_experts_per_tok"] = top_k
            notes.append(f"model_config_alias:top_k_experts={top_k}")
    for holder in (normalized, normalized.get("text_config")):
        if not isinstance(holder, Mapping):
            continue
        frequency = holder.get("moe_layer_freq")
        if isinstance(frequency, list):
            layers = _int(holder.get("num_hidden_layers") or normalized.get("num_hidden_layers"))
            if not layers:
                continue
            # MiniMax declares the routed/dense layer plan as a per-layer list.
            # Carry it as the explicit MoE layer set the model plan consumes.
            if holder is normalized:
                updated = dict(holder)
            else:
                updated = dict(holder)
            updated.pop("moe_layer_freq", None)
            updated["moe_layers_enum"] = [index for index, value in enumerate(frequency)
                                          if value and index < layers]
            if holder is normalized:
                normalized = updated
            else:
                normalized["text_config"] = updated
            notes.append(f"model_config_alias:moe_layer_freq_list->moe_layers_enum:{len(updated['moe_layers_enum'])}")
    if notes:
        return normalized, notes
    return str(path), []
def _compose(declaration: Mapping[str, Any], model: Mapping[str, Any],
             hardware: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    from mindie_sim.compose import compose_case
    from mindie_sim.schema.common import ModelingError
    phase = str(declaration["phase"])
    tp, dp, ep = int(declaration["tp"]), int(declaration["dp"]), int(declaration["ep"])
    prompt = int(declaration["prompt_tokens"])
    output = int(declaration["output_tokens"])
    concurrency = int(declaration["concurrency"])
    model_input, model_notes = _compose_model_input(model)
    try:
        case = compose_case(
            model_input,
            {
                "sku": hardware["sku"],
                "topology_preset": hardware["topology_preset"],
                "num_devices": len(declaration["nodes"]) * int(hardware["ranks_per_node"]),
                "ranks_per_node": int(hardware["ranks_per_node"]),
            },
            tp=tp, dp=dp, ep=ep, pp=int(declaration["pp"]),
            prompt_tokens=prompt, output_tokens=output, concurrency=concurrency,
            prefix_tokens=int(declaration["prefix_tokens"]),
            max_num_seqs=declaration.get("max_num_seqs"),
            max_num_batched_tokens=declaration.get("max_num_batched_tokens"),
            max_model_len=declaration.get("max_model_len"),
            block_size=int(declaration.get("block_size") or 128),
            enable_chunked_prefill=(True if declaration.get("enable_chunked_prefill") is None
                                    else bool(declaration.get("enable_chunked_prefill"))),
            graph_capture_mode=str(declaration.get("graph_mode") or "none"),
            mtp_proposal_tokens=int(declaration.get("mtp_proposal_tokens") or 0),
            mtp_acceptance_length=1.0,
            enable_shared_expert_dp=bool(declaration.get("enable_shared_expert_dp")),
            quant=model.get("quant_spec") or model.get("quant"),
        )
        sizes = declaration.get("graph_capture_sizes") or ()
        kv_dtype = _normalize_kv_dtype(declaration.get("kv_cache_dtype"))
        indexer_dtype = (_normalize_kv_dtype(declaration.get("indexer_kv_dtype"))
                         if str(declaration.get("model_path")) == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4"
                         else None)
        additional = declaration.get("additional_config")
        additional = dict(additional) if isinstance(additional, Mapping) else {}
        changed = bool(additional or declaration.get("multistream_overlap_shared_expert")
                       or declaration.get("gpu_memory_utilization") is not None
                       or indexer_dtype)
        if additional:
            metadata = dict(case.get("runtime", {}).get("metadata") or {})
            metadata["additional_config"] = additional
            case["runtime"]["metadata"] = metadata
        if declaration.get("multistream_overlap_shared_expert"):
            case["runtime"]["multistream_overlap_shared_expert"] = True
        gpu = declaration.get("gpu_memory_utilization")
        if isinstance(gpu, (int, float)) and not isinstance(gpu, bool) and 0 < float(gpu) <= 1:
            case["runtime"]["gpu_memory_utilization"] = float(gpu)
        if ((sizes and str(case.get("runtime", {}).get("graph_capture_mode")) == "full")
                or kv_dtype or changed):
            if sizes and str(case.get("runtime", {}).get("graph_capture_mode")) == "full":
                case["runtime"]["graph_capture_keys"] = sorted({int(item) for item in sizes})
            if kv_dtype:
                case["model"]["kv_dtype"] = kv_dtype
                quant = case["model"].get("quant")
                if isinstance(quant, Mapping):
                    quant = dict(quant)
                    quant["kv_dtype"] = kv_dtype
                    case["model"]["quant"] = quant
            if indexer_dtype:
                quant = case["model"].get("quant")
                if isinstance(quant, Mapping):
                    quant = dict(quant)
                    quant["index_dtype"] = indexer_dtype
                    case["model"]["quant"] = quant
                metadata = dict(case.get("runtime", {}).get("metadata") or {})
                metadata["attention_config"] = dict(declaration.get("attention_config") or {})
                metadata["indexer_kv_dtype"] = indexer_dtype
                case["runtime"]["metadata"] = metadata
            from mindie_sim.prediction.structure import parse_case
            parse_case(case)
    except (ModelingError, ValueError, KeyError, TypeError) as exc:
        return None, model_notes + [f"case_composition_rejected:{exc}"]
    return case, model_notes
def resolve_campaign_case(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Resolve a fleet row to a probe-shaped sim case from its own declaration.
    Returns ``None`` outside the two owned suites.  In-scope rows that cannot be
    declared return ``{"ok": False, "diagnostics": [...], "needed": [...]}``.
    The ``ok`` mapping is directly usable by
    ``fleet_operator_modeling._predict_body`` (same keys as ``_resolve_probe``).
    """
    scope = _scope(row)
    if scope is None:
        return None
    declaration = (_campaign_declaration(scope, row) if scope["kind"] == "campaign"
                   else _rack_declaration(scope, row))
    if "ok" in declaration:
        return declaration
    source = dict(declaration["source"])
    source["hardware"] = []
    diagnostics: list[str] = []
    needed: list[str] = []
    if declaration.get("population_basis") == "mixed_multiturn_decode_tpot":
        diagnostics.append("mixed_window_decode_population:profile_window_contains_prefill_and_decode")
    model = _model_config(str(declaration["model_path"]))
    if model is None:
        return _failure([f"model_config_not_in_catalog:{Path(str(declaration['model_path'])).name}"],
                        ["weights catalog config.json for the declared model_path"], source)
    source["rank_export"] = str(declaration.get("rank_export") or "primary")
    source["model"] = {
        "path": model["config_path"], "sha256": model["config_sha256"],
        "quant": model.get("quant"), "quant_source": model.get("quant_source"),
        "quant_representation": model.get("quant_representation"),
        "weight_classes": dict(model.get("weight_classes") or {}),
        "expert_weight_classes": dict(model.get("expert_weight_classes") or {}),
        "heterogeneous_weight_classes": (
            len([key for key in (model.get("weight_classes") or {}) if key not in {"unknown"}]) > 1
            and not model.get("quant_represented")
        ),
    }
    if source["model"]["heterogeneous_weight_classes"]:
        diagnostics.append("quant_policy_reduced_to_dominant_weight_class")
    elif str(model.get("quant_representation") or "").startswith("split:"):
        diagnostics.append(str(model["quant_representation"]))
    hardware = _resolve_hardware(declaration["nodes"], declaration.get("device_memory_mib"))
    if hardware is None or hardware.get("sku") is None:
        candidates = list((hardware or {}).get("candidates") or [])
        source["hardware_candidates"] = candidates
        diagnostic = ("hardware_sku_ambiguous_catalogue_capacity" if len(candidates) > 1
                      else "hardware_sku_not_declared_for_nodes")
        return _failure([diagnostic] + [f"candidate:{item}" for item in candidates],
                        ["per-host SKU/npu-smi evidence or a unique catalogue capacity match"], source)
    source["hardware"] = hardware["evidence"]
    source["hardware_identity"] = {
        "sku": hardware["sku"], "device_name": hardware["device_name"],
        "hbm_mib": hardware["hbm_mib"],
        "reported_device_memory_mib": hardware.get("reported_device_memory_mib"),
        "identity_basis": hardware.get("identity_basis"),
        "catalogue_candidates": list(hardware.get("candidates") or []),
        "ranks_per_node": hardware["ranks_per_node"],
        "topology_preset": hardware["topology_preset"],
    }
    dp = int(declaration["dp"])
    concurrency = int(declaration["concurrency"])
    sequences = max(1, (concurrency + dp - 1) // dp)
    phase = str(declaration["phase"])
    physical = source.get("physical_rank") if isinstance(source.get("physical_rank"), Mapping) else {}
    measurement_role = ("idle" if declaration.get("rank_export") == "idle_dp_rank"
                        else "active")
    active_rank = source.get("active_rank") if isinstance(source.get("active_rank"), Mapping) else {}
    idle_rank = source.get("idle_rank") if isinstance(source.get("idle_rank"), Mapping) else {}
    if measurement_role == "active" and not active_rank:
        active_rank = physical
    if measurement_role == "idle" and not idle_rank:
        idle_rank = physical
    glm51_source = str(declaration.get("model_path")) == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4"
    normal_body_eligible = True
    body_sequences = None
    if (glm51_source and phase == "decode" and concurrency == 1 and dp == 4
            and int(declaration["tp"]) == 4 and int(declaration["ep"]) == 16
            and active_rank.get("rank_observed") is True
            and 0 <= int(active_rank.get("dp_index", -1)) < dp):
        body_sequences = [0] * dp
        body_sequences[int(active_rank["dp_index"])] = 1
    mtp = int(declaration.get("mtp_proposal_tokens") or 0)
    if phase == "prefill":
        tokens = int(declaration["prompt_tokens"])
        tokens_basis = "declared_prefill_prompt"
    elif mtp > 0:
        tokens = 1 + mtp
        tokens_basis = "declared_speculative_policy_bound"
    else:
        tokens = 1
        tokens_basis = "nominal_decode_one_token"
    context = 0 if phase == "prefill" else int(declaration["prompt_tokens"])
    declared_geometry = {
        "phase": phase, "tokens_per_sequence": tokens,
        "sequences_per_replica": sequences, "sequences_upper_bound": sequences,
        "sequences_observed": False, "context_tokens": context,
        "concurrency": concurrency, "dp": dp,
        "query_rows": sequences * tokens if phase == "decode" else int(declaration["prompt_tokens"]),
        "sequences_formula": "ceil(declared_concurrency / declared_dp)",
        "population_basis": declaration.get("population_basis"),
        "batch_basis": "declared_concurrency_over_dp_upper_bound",
        "rank_batch_observed": False,
        "mtp_proposal_tokens": mtp,
        "tokens_basis": tokens_basis,
        "actual_q_observed": False,
        "rank_export": str(declaration.get("rank_export") or "primary"),
    }
    if glm51_source:
        declared_geometry.update({
            "measurement_role": measurement_role,
            "normal_body_eligible": normal_body_eligible,
            "body_sequences": body_sequences,
            "physical_rank": dict(physical) or None,
            "active_physical_rank": dict(active_rank) or None,
            "idle_physical_rank": dict(idle_rank) or None,
        })
    if declaration.get("rank_export") == "idle_dp_rank":
        diagnostics.append("rank_export_label:idle_dp_rank")
    row_geometry = row.get("geometry") if isinstance(row.get("geometry"), Mapping) else {}
    for key in ("tp", "dp", "ep"):
        declared = declaration[key]
        observed = _int(row_geometry.get(key))
        if observed is not None and observed != declared:
            # Rack rows can carry a rank index in geometry.dp; the declaration
            # wins and the discrepancy stays visible on the result.
            diagnostics.append(f"row_{key}_{observed}_disagrees_with_declaration_{declared}")
    model_for_compose = dict(model)
    if model.get("quant_represented") and model.get("quant_weight_family"):
        model_for_compose["quant_spec"] = _quant_spec_mapping(
            str(model["quant_weight_family"]), str(model.get("quant_expert_family")
                                                    or model["quant_weight_family"]),
            dict(model.get("quant_overrides") or {}),
            str(declaration.get("kv_cache_dtype") or ""))
    case, errors = _compose(declaration, model_for_compose, hardware)
    if case is None:
        return _failure(errors, ["valid declared case composition"], source)
    diagnostics.extend(errors)
    runtime = case.get("runtime") if isinstance(case.get("runtime"), Mapping) else {}
    for axis in ("tp", "dp", "ep", "pp"):
        if _int(runtime.get(axis)) is not None and _int(runtime.get(axis)) != int(declaration[axis]):
            return _failure([f"composed_{axis}_{runtime.get(axis)}_disagrees_with_declaration_{declaration[axis]}"],
                            [], source)
    if str(declaration.get("model_path")) == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4" and source.get("image"):
        metadata = dict(runtime.get("metadata") or {})
        metadata["image"] = str(source["image"])
        metadata["image_identity"] = str(source["image"])
        metadata["image_identity_source"] = "case_spec.image"
        metadata["image_id_status"] = "unknown_not_parsed"
        case["runtime"]["metadata"] = metadata
        runtime = case["runtime"]
    identity_source = {
        key: source[key] for key in (
            "case_spec", "manifest", "cell_launch", "case_declaration", "cell_launcher",
            "model_path", "model", "hardware_identity", "device_memory",
        ) if key in source
    }
    if str(declaration.get("model_path")) == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4" and source.get("image"):
        identity_source["image"] = str(source["image"])
        identity_source["image_identity_source"] = "case_spec.image"
        identity_source["image_id_status"] = "unknown_not_parsed"
    identity_geometry = {key: value for key, value in declared_geometry.items()
                         if key != "rank_export"}
    identity = hashlib.sha256(json.dumps({
        "source": identity_source, "phase": phase,
        "parallel": {axis: int(declaration[axis]) for axis in ("tp", "dp", "ep", "pp")},
        "geometry": identity_geometry,
        "graph_mode": declaration.get("graph_mode"),
        "runtime_features": {
            "additional_config": declaration.get("additional_config") or {},
            "enable_shared_expert_dp": declaration.get("enable_shared_expert_dp"),
            "multistream_overlap_shared_expert": declaration.get("multistream_overlap_shared_expert"),
            "gpu_memory_utilization": declaration.get("gpu_memory_utilization"),
            "block_size": declaration.get("block_size"),
            "enable_prefix_caching": declaration.get("enable_prefix_caching"),
            "prefix_tokens": declaration.get("prefix_tokens"),
            "kv_cache_dtype": declaration.get("kv_cache_dtype"),
            "enable_chunked_prefill": declaration.get("enable_chunked_prefill"),
            **({"attention_config": declaration.get("attention_config") or {},
                "indexer_kv_dtype": declaration.get("indexer_kv_dtype"),
                "image": source.get("image"),
                "image_identity_source": "case_spec.image",
                "image_id_status": "unknown_not_parsed"}
               if str(declaration.get("model_path")) == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4" else {}),
        },
    }, sort_keys=True, default=str).encode()).hexdigest()
    population = {
        "sequences_per_replica": sequences, "tokens_per_sequence": tokens,
        "context_tokens": context, "forward_count": None,
        "context_basis": "declared_launch_isv",
        "batch_basis": "declared_concurrency_over_dp_upper_bound",
    }
    return {
        "ok": True, "status": "modeled", "case": case,
        "case_path": model["config_path"], "phase": phase,
        "deployment_sha256": identity,
        "structural_sha256": hashlib.sha256(
            json.dumps(case, sort_keys=True, default=str).encode()).hexdigest(),
        "graph_mode": declaration.get("graph_mode"),
        "mtp_proposal_tokens": int(declaration.get("mtp_proposal_tokens") or 0),
        "speculative_method": declaration.get("speculative_method"),
        "parallel": {axis: int(declaration[axis]) for axis in ("tp", "dp", "ep", "pp")},
        "sequences": sequences, "tokens": tokens,
        "body_sequences": body_sequences,
        "measurement_role": measurement_role,
        "normal_body_eligible": normal_body_eligible,
        "physical_rank": dict(physical) or None,
        "active_physical_rank": dict(active_rank) or None,
        "idle_physical_rank": dict(idle_rank) or None,
        "context": context, "context_source": "declared_launch_isv",
        "sku": hardware["sku"], "runtime": dict(runtime),
        "population": population, "populations": [population],
        "frames": [], "calibration": {"removed_service_regimes": [],
                                      "removed_device_rates": [], "labels": {}},
        "source_role": ("campaign_launch_declaration" if declaration["kind"] == "campaign"
                        else "rack_launch_declaration"),
        "diagnostics": diagnostics,
        "geometry": declared_geometry,
        "workload": {
            "prompt_tokens": int(declaration["prompt_tokens"]),
            "output_tokens": int(declaration["output_tokens"]),
            "prefix_tokens": int(declaration["prefix_tokens"]),
            "concurrency": concurrency,
        },
        "source_image": str(source.get("image") or ""),
        "source": source,
    }
