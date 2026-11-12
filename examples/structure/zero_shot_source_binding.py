"""Source/config binding and declared cache-row normalization.

[Role] Bind a retained campaign to its actual HF config, weights and status,
  and compose same-model template declarations with explicit source overrides.
[Invariants] Foreign/cross-version sources do not inherit template cache rows or
  their dependent lowering.  Only source-declared KV overrides replace rows.
[Side-Effect Policy] Read-only local files; returns a new case mapping.
"""
from __future__ import annotations
from functools import lru_cache
import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence
from dataclasses import replace


def _main_module():
    try: from . import zero_shot_piecewise_validation as module
    except ImportError: import zero_shot_piecewise_validation as module
    return module


@lru_cache(maxsize=1024)
def _source_binding(cell_id: str, tp: int, dp: int, ep: int) -> tuple[Path | None, str, str, Path | None, Path | None]:
    try: from .zero_shot_native_windows import _model_config
    except ImportError: from zero_shot_native_windows import _model_config
    main = _main_module(); _load_json = main._load_json
    for root in main.WORKSTREAM_ROOTS:
        for cell_dir in sorted((Path(root) / 'out').glob('*/*')):
            if f'{cell_dir.parent.name}_{cell_dir.name}' != cell_id: continue
            case_dir = cell_dir.parent; status = _load_json(case_dir / 'status.json') or {}
            nodes = (status.get('spec') or {}).get('nodes') if isinstance(status.get('spec'), Mapping) else ()
            host = str(next(iter(nodes), '') or '')
            raw_case, config, error, provenance = _model_config({'tp': tp, 'dp': dp, 'ep': ep}, case_dir, host)
            path = str(provenance.get('weight_config_path') or ''); sha = str(provenance.get('weight_config_sha256') or ''); weight = str(provenance.get('launch_model_dir') or provenance.get('weight_model_dir') or '')
            if path and sha:
                local = next((Path('/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108') / Path(weight).name for _ in (1,) if weight and (Path('/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108') / Path(weight).name).is_dir()), None)
                return Path(path), sha, sha, (local or (Path(weight) if weight else None)), case_dir
    return None, '', '', None, None
def _w_category(category: str) -> str:
    text = str(category); rules = (("shared_experts", "shared_expert"), ("experts", "routed_expert"), ("self_attn.q_a", "mla.q_a"), ("self_attn.q_b", "mla.q_b"), ("self_attn.o_proj", "mla.o"), ("self_attn.kv_a", "mla.kv_a"), ("self_attn.kv_b", "mla.kv_b"), ("indexer.k_norm", ""), ("indexer.wq_b", "indexer"), ("indexer.wk", "indexer.pool_projection"), ("indexer.weights_proj", "indexer.weights"), ("mlp.gate_proj", "dense_mlp"), ("mlp.down_proj", "dense_mlp"), ("mlp.up_proj", "dense_mlp"), ("mlp.gate", "router"))
    return next((cat for token, cat in rules if token in text), "norm" if ("layernorm" in text or text.endswith(".norm")) else "")
def _header_source(spec: Any) -> Path | None:
    if spec.source_header_archive is not None: return spec.source_header_archive
    root = os.environ.get('MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT', '')
    if root and spec.source_weight_dir is not None:
        path = Path(root) / f'{Path(spec.source_weight_dir).name}.json'
        if path.is_file(): return path
    return None
def _norm_role(category: str) -> str:
    text = str(category); rules = (("input_layernorm", "attn_norm"), ("post_attention_layernorm", "ffn_norm"), ("q_a_layernorm", "q_a"), ("kv_a_layernorm", "kv_a"), ("indexer.k_norm", "indexer_k"), ("shared_head.norm", "shared_head"), ("enorm", "enorm"), ("hnorm", "hnorm"))
    return next((role for token, role in rules if token in text), "final" if text.endswith("model.norm") else "")
def _apply_native_quant(spec: Any, raw: dict[str, Any]) -> dict[str, Any]:
    main = _main_module(); _load_json = main._load_json; _cohort_case = main._cohort_case
    root = spec.source_weight_dir
    if root is None or not Path(root).is_dir(): return raw
    try: from .fleet_weight_quantization import bind_deployed_weight_units, load_deployed_module_quant
    except ImportError: from fleet_weight_quantization import bind_deployed_weight_units, load_deployed_module_quant
    try: from .fleet_campaign_case import _quant_spec_mapping
    except ImportError: from fleet_campaign_case import _quant_spec_mapping
    source = _header_source(spec); bound = None; note = 'header_source_absent' if spec.source_header_archive is not None else 'header_source_none'; scheme = load_deployed_module_quant(root)
    if source is not None:
        try: bound = bind_deployed_weight_units(root, header_source=source)
        except (OSError, ValueError, KeyError, TypeError) as error: note = f'header_source_unreadable:{type(error).__name__}'
        else: note = f"header_source_ineligible:{bound.get('reason') or bound.get('status')}" if bound.get('status') != 'mapped' else 'header_source_bound'; bound = None if bound.get('status') != 'mapped' else bound
    record = bound or scheme; auth = ((raw.get('runtime') or {}).get('metadata') or {}).get('template_quant_authority'); declared_index = next((json.loads(n.split(':', 1)[1]) for n in spec.notes if n.startswith('indexer_weight_formats:')), {})
    if bound is None and auth in ('foreign_family_rejected', 'cross_version_template_rejected'): rt = dict(raw.get('runtime') or {}); meta = dict(rt.get('metadata') or {}); meta['quant_source_note'] = note; meta['checkpoint_storage_dtypes'] = {'norm': 'unknown'}; meta['norm_storage'] = {}; meta['norm_runtime'] = {}; meta['norm_storage_bytes'] = {}; meta['norm_runtime_bytes'] = {}; rt['metadata'] = meta; return {**raw, 'runtime': rt}
    prior_quant = raw.get('model', {}).get('quant') if isinstance(raw.get('model'), Mapping) else None
    if isinstance(prior_quant, (list, tuple)):
        try: prior_quant = dict(prior_quant)
        except (TypeError, ValueError): prior_quant = None
    source_key = _model_key(str(spec.source_config.parent.name) if spec.source_config else ''); prior_key = _model_key(str(raw.get('model', {}).get('catalog_key') or (prior_quant or {}).get('source', {}).get('checkpoint') or '')) if isinstance(raw.get('model'), Mapping) else ''
    if bound is None and isinstance(prior_quant, Mapping) and not declared_index and source_key and source_key == prior_key: rt = dict(raw.get('runtime') or {}); meta = dict(rt.get('metadata') or {}); meta['quant_source_note'] = note; meta['template_quant_authority'] = 'same_family_template_conditional'; rt['metadata'] = meta; return {**raw, 'runtime': rt}
    allowed_index = {'indexer': 'FP8', 'indexer.pool_projection': 'BF16', 'indexer.weights': 'BF16'}
    for role, fmt in declared_index.items():
        if role not in allowed_index or str(fmt).upper() != allowed_index[role]: raise ValueError(f'indexer_weight_format_unsupported:{role}:{fmt}')
    if record.get('status') != 'mapped' and not declared_index: return raw
    counts = record.get('weight_counts') or {}; hf_cfg = raw.get('model', {}).get('hf_config') or {}; qconf = hf_cfg.get('quantization_config') if isinstance(hf_cfg, Mapping) else {}; expert = 'mxfp4' if int(counts.get('W4') or 0) > 0 or 'fp4' in str((qconf or {}).get('expert_dtype') or '').lower() else 'mxfp8'
    if isinstance(prior_quant, Mapping) and bound is None: quant = dict(prior_quant)
    elif record.get('status') != 'mapped':
        try: from mindie_sim.prediction.structure import parse_case; quant = dict(parse_case({**raw, 'model': raw.get('model', {})}).model.quant.to_dict())
        except Exception: quant = _quant_spec_mapping('mxfp8', expert)
    else: quant = _quant_spec_mapping('mxfp8', expert)
    overrides = {}; checkpoint_storage = {}; norm_storage = {}; norm_runtime = {}
    for module in (record.get('modules') or ()) if record.get('status') == 'mapped' else ():
        if module.get('role') not in (None, 'weight') or not (category := _w_category(module.get('category') or '')): continue
        scheme_name = str(module.get('scheme') or ''); stored = str(module.get('stored_dtype') or '') if bound else ''
        fmt = 'bf16' if category == 'norm' else 'mxfp4' if scheme_name == 'W4A4_MXFP4' else 'fp8_e4m3' if scheme_name == 'W8A8_MXFP8' else 'fp32' if stored == 'F32' else 'bf16'
        act = 'bf16' if category == 'norm' else 'mxfp4' if fmt == 'mxfp4' else 'fp8_e4m3' if fmt == 'fp8_e4m3' else 'fp32' if fmt == 'fp32' else 'bf16'
        checkpoint_storage[category] = stored or 'unknown'; role = _norm_role(module.get('category') or ''); norm_storage[role] = stored if role and stored in ('F32', 'BF16') else norm_storage.get(role); overrides[category] = (('weight_format', fmt), ('activation_format', act)) if category != 'norm' and not (category in ('indexer.pool_projection', 'indexer.weights') and not stored) else None
    declared_abi = next((json.loads(n.split(':', 1)[1]) for n in spec.notes if n.startswith('norm_runtime_abi:')), {}); norm_runtime.update({str(k): str(v).upper() for k, v in declared_abi.items() if str(v).upper() in ('BF16', 'F32')}); overrides.update({k: (('weight_format', 'fp8_e4m3' if v == 'FP8' else 'bf16'), ('activation_format', 'fp8_e4m3' if v == 'FP8' else 'bf16')) for k, v in declared_index.items()}); quant['category_overrides'] = {k: v for k, v in overrides.items() if v}; quant['norm_storage'] = {k: v for k, v in norm_storage.items() if v}; quant['norm_runtime'] = {k: v for k, v in norm_runtime.items() if v}
    cohort = _load_json(_cohort_case(spec)) if _cohort_case(spec) is not None else None
    indexer_kv_dtype = ''
    if isinstance(cohort, Mapping):
        if str(cohort.get('kv_cache_dtype') or '').lower() == 'fp8': quant['kv_dtype'] = 'fp8_e4m3'
        if str((cohort.get('attention_config') or {}).get('indexer_kv_dtype') or '').lower() == 'fp8':
            quant['index_dtype'] = 'fp8_e4m3'
            indexer_kv_dtype = 'fp8_e4m3'
    wq_scale_count = sum(int(module.get('count') or 0) for module in (scheme.get('modules') or ())
                         if module.get('role') == 'scale'
                         and str(module.get('category') or '').endswith('self_attn.indexer.wq_b')
                         and int(module.get('count') or 0) > 0)
    rt = dict(raw.get('runtime') or {}); meta = dict(rt.get('metadata') or {}); hf = (raw.get('model', {}).get('hf_config') or {}); hidden = int(hf.get('hidden_size') or (hf.get('text_config') or {}).get('hidden_size') or 0); meta['checkpoint_storage_dtypes'] = checkpoint_storage; meta['quant_source_note'] = note; meta['template_quant_authority'] = 'bound_source_header' if bound else ('same_family_template_conditional' if raw.get('model', {}).get('quant') else 'none'); meta['norm_storage'] = {k: v for k, v in norm_storage.items() if v}; meta['indexer_weight_formats'] = {k: (checkpoint_storage.get(k) or 'unknown') for k in ('indexer.pool_projection', 'indexer.weights')}; meta['indexer_runtime_formats'] = dict(declared_index); meta['norm_runtime'] = {k: v for k, v in norm_runtime.items() if v}; meta['norm_storage_bytes'] = {'attn_norm': (4 if norm_storage.get('attn_norm') == 'F32' else 2) * hidden} if hidden and norm_storage.get('attn_norm') else {}; meta['norm_runtime_bytes'] = {'attn_norm': (4 if norm_runtime.get('attn_norm') == 'F32' else 2) * hidden} if hidden and norm_runtime.get('attn_norm') else {}; meta['norm_runtime_assumption'] = None if norm_runtime else 'bf16_default_assumption'; meta['indexer_kv_dtype'] = indexer_kv_dtype; meta['indexer_query_scale_present'] = bool(wq_scale_count); meta['indexer_query_scale_source'] = 'wq_b.weight_scale' if wq_scale_count else ''; meta['indexer_query_scale_dtype'] = 'fp32' if wq_scale_count else ''; rt['metadata'] = meta
    return {**raw, 'runtime': rt, 'model': {**raw.get('model', {}), 'quant': quant}}
def _header_alias(raw: Mapping[str, Any]) -> Path | None:
    value = raw.get('weight_header_archive') or raw.get('header_archive') or raw.get('source_header_archive') or raw.get('header_source')
    return Path(str(value)) if value else None
def _bind_original_deployment(spec: Any, raw: Mapping[str, Any]) -> Any:
    src, sha, deploy, weight, case_dir = _source_binding(spec.cell_id.split(':')[-1], spec.tp, spec.dp, spec.ep); archive = spec.source_header_archive
    epath = raw.get('source_config') or raw.get('model_config_path'); esha = str(raw.get('source_config_sha256') or raw.get('model_config_sha256') or '')
    if src is None: return replace(spec, source_reject_reason='deploy_binding_unavailable') if (epath or esha) else spec
    if not epath and not esha: return replace(spec, source_config=src, source_config_sha256=sha, source_deploy_sha256=deploy, source_weight_dir=weight, source_case_dir=case_dir, source_header_archive=archive, require_source=True)
    path = Path(str(epath)) if epath else None
    if path is None or not path.is_file(): return replace(spec, require_source=True, source_reject_reason='source_override_path_invalid')
    try: actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError: return replace(spec, require_source=True, source_reject_reason='source_override_unreadable')
    allowed = {Path(weight).name} if weight is not None else set(); allowed.add(src.parent.name)
    return replace(spec, source_config=src, source_config_sha256=sha, source_deploy_sha256=deploy, source_weight_dir=weight, source_case_dir=case_dir, require_source=True) if actual == sha and path.parent.name in allowed else replace(spec, require_source=True, source_reject_reason='source_override_contradicts_deployment')
def _model_family(text: Any) -> str:
    match = re.match(r"[a-z]+", str(text or "").lower())
    return match.group(0) if match else ""
def _model_key(text: Any) -> str:
    match = re.search(r"([a-z]+)[._ -]?(\d+)[._-](\d+)", str(text or "").lower())
    return f"{match.group(1)}{match.group(2)}.{match.group(3)}" if match else ""
def _quant_dict(value: Any) -> dict[str, Any] | None:
    try:
        from mindie_sim.catalog.types import QuantSpec
        if isinstance(value, QuantSpec): spec = value
        else:
            raw = dict(value) if isinstance(value, Mapping) else dict(value or ()); spec = QuantSpec(**raw)
        out = spec.to_dict()
        for key in ('output_format', 'runtime_weight_scale_format', 'runtime_weight_scale_bytes', 'runtime_activation_scale_format', 'runtime_int8_weight_metadata'): out[key] = getattr(spec, key)
        return out
    except (TypeError, ValueError, KeyError): return None
def _merge_quant_preset(quant: Mapping[str, Any], declared: Any) -> dict[str, Any]:
    try:
        from mindie_sim.catalog.quant import quant_preset
        base = _quant_dict(quant_preset(str(declared))) or {}
    except (ValueError, TypeError, KeyError): return dict(quant)
    raw_keys = set(quant.keys()) if isinstance(quant, Mapping) else set(); template = _quant_dict(quant) or dict(quant); merged = dict(base)
    for key, value in template.items():
        if key == 'category_overrides':
            categories = {category: dict(fields) for category, fields in (base.get('category_overrides') or {}).items()}
            explicit_globals = raw_keys - {'category_overrides', 'source'}
            for fields in categories.values():
                for field in explicit_globals: fields.pop(field, None)
            for category, fields in (value or {}).items(): categories[category] = {**categories.get(category, {}), **dict(fields)}
            merged['category_overrides'] = categories
        elif key == 'source': merged['source'] = {**dict(base.get('source') or {}), **dict(value or {})}
        elif key not in ('output_format', 'runtime_weight_scale_format', 'runtime_weight_scale_bytes', 'runtime_activation_scale_format', 'runtime_int8_weight_metadata') or key in raw_keys: merged[key] = value
    return merged
def _requested_cache_regions(dtype: str, template: Mapping[str, Any]) -> dict[str, dict[str, Any]] | None:
    """Apply only the regions the requested storage declaration actually owns.

    Packed source cache rows keep their per-region representation; an explicit
    global KV request changes window or compressed storage only where that
    region's ABI is the one being selected.  Unknown requests stay conditional.
    """
    text = str(dtype or "").strip().lower()
    if text in {"bfloat16", "bf16", "float16", "fp16", "float32", "fp32"}:
        dtype = {"bfloat16": "bf16", "bf16": "bf16", "float16": "fp16",
                 "fp16": "fp16", "float32": "fp32", "fp32": "fp32"}[text]
        return {region: {"dtype": dtype} for region in template}
    if text.startswith("fp8"):
        dtype = "fp8_e4m3" if text in {"fp8", "fp8_e4m3"} else text
        return {region: ({**dict(item), "dtype": dtype} if region == "window" else dict(item))
                for region, item in template.items()}
    if text.startswith("fp4"):
        dtype = "fp4_e2m1" if text in {"fp4", "fp4_e2m1"} else text
        return {region: ({**dict(item), "dtype": dtype} if region == "compressed_kv" else dict(item))
                for region, item in template.items()}
    return None


def _cache_bound_lowerings(lowerings: Mapping[str, Any]) -> tuple[str, ...]:
    """Selected mixed-cache lowering keys, by declared implementation identity."""
    out = []
    for key, value in (lowerings or {}).items():
        text = str(value.get("implementation") if isinstance(value, Mapping) else value).lower()
        if ("mixed_quant_sparse_flash_mla" in text or "packaged_mqsmla" in text
                or "mixed_quant_attention" in text):
            out.append(key)
    return tuple(out)


def _source_index_head(raw: Mapping[str, Any]) -> int:
    """Actual HF/architecture index role width, never a display-name rule."""
    model = raw.get("model") if isinstance(raw, Mapping) else None
    hf = model.get("hf_config") if isinstance(model, Mapping) else None
    text = hf.get("text_config") if isinstance(hf, Mapping) else hf
    if isinstance(text, Mapping):
        head = int(text.get("index_head_dim") or 0)
        roles = text.get("index_source_layer_ids") or []
        if head > 0 and (roles or int(text.get("index_topk") or 0) > 0):
            return head
    try:
        from mindie_sim.schema.model import ModelSpec
        resolved = ModelSpec.from_mapping(model) if isinstance(model, Mapping) else None
        mla = getattr(resolved, "mla", None)
        if mla is not None and int(getattr(mla, "index_head_dim", 0) or 0) > 0:
            return int(mla.index_head_dim)
    except (ValueError, TypeError, KeyError):
        return 0
    return 0


def _packed_source_cache_capability(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    """Typed A5 hardware capability + actual V4.1 MLA/cache-role/quant plan.

    No role prose, display name, image id or optional lowering substring is a
    capability selector.  Hardware is the normalized deployment product; model
    semantics come from the normal simulator HF architecture resolution.
    """
    try:
        from mindie_sim.schema.hardware import Hardware
        from mindie_sim.schema.model import ModelSpec
        hardware = Hardware.from_mapping(raw.get("machine") or {})
        model = ModelSpec.from_mapping(raw.get("model") or {})
    except (ValueError, TypeError, KeyError):
        return None
    if str(hardware.arch_family or "").strip().upper() != "A5": return None
    hf = (raw.get("model") or {}).get("hf_config") if isinstance(raw.get("model"), Mapping) else None
    hf = hf if isinstance(hf, Mapping) else {}
    hf_type = str(hf.get("model_type") or ((hf.get("text_config") or {}).get("model_type")
                                            if isinstance(hf.get("text_config"), Mapping) else "") or "").strip().lower()
    if hf_type != "deepseek_v41": return None
    mla = getattr(model, "mla", None)
    if getattr(model, "attention", "") != "mla" or mla is None: return None
    head = int(getattr(mla, "v_head_dim", 0) or 0)
    if head != 512 or int(getattr(mla, "qk_nope_head_dim", 0) or 0) != 448 or int(getattr(mla, "qk_rope_head_dim", 0) or 0) != 64:
        return None
    plans = tuple(getattr(model, "layer_plans", ()) or ())
    if not any(str(getattr(plan, "cache_kind", "")) == "window_compressed"
               and int(getattr(plan, "compress_ratio", 0) or 0) > 0 for plan in plans):
        return None
    geometry = {"head_dim": head,
                "original_row_bytes": head + (head // 32) * 2,
                "compressed_row_bytes": head // 2 + (head // 16) * 2}
    index_head = _source_index_head(raw)
    if index_head > 0:
        geometry.update(index_head_dim=index_head,
                        index_row_bytes=index_head // 2 + index_head // 32)
    return {"role": "window_compressed_mla", "hardware_arch": str(hardware.arch_family),
            "geometry": geometry, "model_architecture": hf_type,
            "binary_identity": "source-declared capability; exact deployed binary not re-proven"}


def _packed_cache_regions(capability: Mapping[str, Any], template: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Derive coherent packed rows from the declared source geometry."""
    from mindie_sim.catalog.cache_format import CacheFormat
    geometry = capability.get("geometry") or {}
    head = int(geometry.get("head_dim") or 0)
    window = {"dtype": "fp8_e4m3", "group_size": 32, "scale_dtype": "bf16"}
    compressed = {"dtype": "fp4_e2m1", "group_size": 16, "scale_dtype": "bf16"}
    expected_window = int(geometry.get("original_row_bytes") or 0)
    expected_compressed = int(geometry.get("compressed_row_bytes") or 0)
    actual_window = CacheFormat(**window).row_bytes(head)
    actual_compressed = CacheFormat(**compressed).row_bytes(head)
    if expected_window and actual_window != expected_window: return {}, {"window": expected_window, "derived": actual_window}
    if expected_compressed and actual_compressed != expected_compressed: return {}, {"compressed_kv": expected_compressed, "derived": actual_compressed}
    regions = {"window": window, "compressed_kv": compressed}
    index_head = int(geometry.get("index_head_dim") or 0)
    if index_head:
        index = {"dtype": "uint8", "group_size": 32, "scale_dtype": "uint8", "packed_elements": 2}
        expected_index = int(geometry.get("index_row_bytes") or 0)
        actual_index = CacheFormat(**index).row_bytes(index_head)
        if not expected_index or actual_index == expected_index: regions["index_k"] = index
    for key in template:
        if key == "indexer" and "index_k" in regions: continue
        if key not in regions: regions[key] = dict(template[key])
    return regions, {"window": expected_window or actual_window,
                     "compressed_kv": expected_compressed or actual_compressed,
                     "index_k": int(geometry.get("index_row_bytes") or 0)}


def _remove_template_cache_branch(raw: Mapping[str, Any], *, basis: str,
                                  template: Any = None, removed: Sequence[str] = ()) -> dict[str, Any]:
    model = dict(raw.get("model") or {})
    metadata = dict(model.get("metadata") or {})
    regions = metadata.pop("cache_representations", None)
    if metadata: model["metadata"] = metadata
    else: model.pop("metadata", None)
    runtime = dict(raw.get("runtime") or {})
    kernels = dict(runtime.get("kernels") or {})
    lowerings = dict(kernels.get("lowerings") or {})
    dropped = tuple(dict.fromkeys((*removed, *_cache_bound_lowerings(lowerings)))) if basis != "source_declared_override" else tuple(removed)
    for key in dropped:
        lowerings.pop(key, None)
    if lowerings or "lowerings" in kernels:
        kernels["lowerings"] = lowerings
        runtime["kernels"] = kernels
    meta = dict(runtime.get("metadata") or {})
    meta["source_cache_declaration"] = {"basis": basis,
                                        "template_regions": regions if regions is not None else template,
                                        "removed_lowerings": list(dropped)}
    runtime["metadata"] = meta
    return {**raw, "model": model, "runtime": runtime}


def _apply_source_cache_declaration(spec: Any, raw: Mapping[str, Any], *,
                                    compatible: bool, prior_model: Mapping[str, Any]) -> dict[str, Any]:
    """Compose registered cache rows with the selected source producer boundary.

    The outer ``kv_cache_dtype`` request is recorded separately.  A selected
    packed-cache lowering owns the per-region rows (window and compressed MLA),
    even when the outer request says bfloat16: the deployed A5 capability
    overrides that request.  A plain/no-packed source applies the request to
    the regions it actually owns; it does not rewrite every region blindly.
    """
    main = _main_module(); _load_json = main._load_json; _cohort_case = main._cohort_case
    template_regions = dict((prior_model.get("metadata") or {}).get("cache_representations") or {})
    if not compatible:
        return _remove_template_cache_branch(raw, basis="incompatible_source_template_branch_removed",
                                             template=template_regions)
    cohort = _load_json(_cohort_case(spec)) if _cohort_case(spec) is not None else None
    declared = str((cohort or {}).get("kv_cache_dtype") or "").strip().lower() if isinstance(cohort, Mapping) else ""
    runtime = dict(raw.get("runtime") or {})
    kernels = dict(runtime.get("kernels") or {})
    lowerings = dict(kernels.get("lowerings") or {})
    selected = _cache_bound_lowerings(lowerings)
    capability = _packed_source_cache_capability(raw)
    model = dict(raw.get("model") or {})
    metadata = dict(model.get("metadata") or {})
    meta = dict(runtime.get("metadata") or {})
    if capability:
        regions, layout = _packed_cache_regions(capability, template_regions)
        if regions:
            metadata["cache_representations"] = regions
            metadata["cache_representation_basis"] = "source_packed_cache_capability"
            meta["source_cache_declaration"] = {
                "basis": "source_packed_cache_capability_overrides_requested",
                "requested_kv_cache_dtype": declared or None,
                "regions": regions, "selected_lowerings": list(selected),
                "requested_override_applied": False,
                "storage_layout": layout,
                "capability_role": capability.get("role"),
                "source_geometry": capability.get("geometry"),
                "binary_identity": capability.get("binary_identity"),
                "basis_note": "declared_source_capability; exact deployed binary not re-proven"}
        else:
            meta["source_cache_declaration"] = {
                "basis": "source_packed_cache_capability_geometry_conditional",
                "requested_kv_cache_dtype": declared or None,
                "regions": template_regions, "selected_lowerings": list(selected),
                "requested_override_applied": False, "storage_layout": layout,
                "capability_role": capability.get("role"),
                "source_geometry": capability.get("geometry")}
    else:
        if not declared or declared in {"auto", "default"}:
            return raw
        regions = _requested_cache_regions(declared, template_regions) or {}
        index_head = _source_index_head(raw)
        if index_head > 0:
            regions["index_k"] = {"dtype": "int8", "group_size": index_head, "scale_dtype": "fp16"}
        if not regions:
            return raw
        metadata["cache_representations"] = regions
        metadata["cache_representation_basis"] = f"requested_kv_cache_dtype_without_packed_capability:{declared}"
        region_dtype = (regions.get("window") or regions.get("compressed_kv") or {}).get("dtype")
        if region_dtype in {"bf16", "fp16", "fp32", "fp8_e4m3", "fp8_e5m2"}:
            model["kv_dtype"] = region_dtype
        removed = _cache_bound_lowerings(lowerings)
        for key in removed: lowerings.pop(key, None)
        if removed:
            kernels["lowerings"] = lowerings; runtime["kernels"] = kernels
        metadata["unmodeled_features"] = [item for item in metadata.get("unmodeled_features") or ()
                                          if "mixed" not in str(item).lower() and "cache" not in str(item).lower()]
        metadata["degraded_submodules"] = [item for item in metadata.get("degraded_submodules") or ()
                                           if "mixed_quant" not in str(item).lower()]
        meta["source_cache_declaration"] = {
            "basis": "requested_kv_cache_dtype_applied_without_packed_capability",
            "requested_kv_cache_dtype": declared, "regions": regions,
            "selected_lowerings": [], "removed_lowerings": list(removed),
            "requested_override_applied": True}
    model["metadata"] = metadata; runtime["metadata"] = meta
    return {**raw, "model": model, "runtime": runtime}




# Forecast source sanitation: target-in-sample service observations are not
# forecast admission.  This runs on the source case before optional cohort
# metadata is merged/stripped, so a rule can inherit its enclosing calibration
# evidence exactly once.  It never edits machine rates, declared supplies,
# replay/execution declarations, model data or template files.
_SERVICE_CONTEXT_KEYS = (
    'calibration_origin', 'evaluation_relation',
    'heldout_observed_values_used_in_fit', 'target_timing_used_to_fit',
)


def _service_context(node: Mapping[str, Any], inherited: Mapping[str, Any]) -> dict[str, Any]:
    context = dict(inherited or {})
    for key in _SERVICE_CONTEXT_KEYS:
        if key in node and not isinstance(node[key], (Mapping, list, tuple)):
            context[key] = node[key]
    for holder_key in ('metadata', 'calibration', 'calibration_evidence', 'provenance'):
        holder = node.get(holder_key)
        if isinstance(holder, Mapping):
            for key in _SERVICE_CONTEXT_KEYS:
                if key in holder and not isinstance(holder[key], (Mapping, list, tuple)):
                    context[key] = holder[key]
    return context


def _target_in_sample_service(origin: Any, relation: Any, heldout: Any,
                              target_fit: Any = None) -> bool:
    """Semantic target-corpus classification; no ids, paths or case names."""
    origin = str(origin or '').strip().lower()
    relation = str(relation or '').strip().lower()
    # A physical-domain fit is an independent microbench/domain calibration,
    # even when its label contains the in_sample token.
    if 'physical_domain_fit' in relation:
        return False
    if relation == 'in_sample':
        return True
    if origin == 'retained_operator_service_in_sample':
        return True
    if origin == 'observed' and heldout is True:
        return True
    if origin == 'observed' and target_fit is True:
        return True
    return False


def _sanitize_forecast_service_rules(raw: Mapping[str, Any], evidence: list | None = None) -> dict[str, Any]:
    """Drop only target-in-sample service observations from a forecast case.

    The returned case is a deep copy.  Legacy inherited enclosing calibration
    metadata is read before the caller's optional cohort overlay strips it.
    Source-declared/out-of-sample services, hardware supply, replay and
    execution declarations remain untouched.
    """
    clean = copy.deepcopy(dict(raw))

    def walk(node: Any, inherited: Mapping[str, Any]) -> None:
        if isinstance(node, dict):
            context = _service_context(node, inherited)
            regimes = node.get('service_regimes')
            if isinstance(regimes, (list, tuple)):
                kept = []
                for rule in regimes:
                    if not isinstance(rule, Mapping):
                        kept.append(rule)
                        continue
                    own = rule.get('provenance')
                    own = dict(own) if isinstance(own, Mapping) else {}
                    own_origin = own.get('calibration_origin')
                    # An explicit source-declared independent service owns its
                    # provenance; do not let an optional enclosing corpus label
                    # erase it.
                    source_declared = bool(own_origin and str(own_origin) != 'observed'
                                           and 'in_sample' not in str(own_origin).lower())
                    if source_declared:
                        origin = own_origin
                        relation = own.get('evaluation_relation')
                        heldout = own.get('heldout_observed_values_used_in_fit')
                        target_fit = own.get('target_timing_used_to_fit')
                    else:
                        origin = own_origin if own_origin is not None else context.get('calibration_origin')
                        relation = own.get('evaluation_relation') if 'evaluation_relation' in own else context.get('evaluation_relation')
                        heldout = own.get('heldout_observed_values_used_in_fit') if 'heldout_observed_values_used_in_fit' in own else context.get('heldout_observed_values_used_in_fit')
                        target_fit = own.get('target_timing_used_to_fit') if 'target_timing_used_to_fit' in own else context.get('target_timing_used_to_fit')
                    if _target_in_sample_service(origin, relation, heldout, target_fit):
                        if evidence is not None:
                            evidence.append({'id': rule.get('id'), 'origin': origin,
                                             'relation': relation, 'heldout': heldout,
                                             'target_fit': target_fit})
                        continue
                    kept.append(rule)
                if isinstance(regimes, tuple):
                    node['service_regimes'] = tuple(kept)
                else:
                    node['service_regimes'] = kept
            for value in list(node.values()):
                walk(value, context)
        elif isinstance(node, list):
            for value in node:
                walk(value, inherited)

    walk(clean, {})
    return clean

def _raw_case_base(spec: Any) -> dict[str, Any]:
    main = _main_module(); CASES_DIR = main.CASES_DIR; _A5_MACH_FILE = main._A5_MACH_FILE
    _MODEL_CFGS = main._MODEL_CFGS; _DSPARK_KEY = main._DSPARK_KEY
    raw = json.loads(spec.model_case.read_text(encoding='utf-8')) if spec.model_case is not None and spec.model_case.exists() else {}
    if spec.source_config is not None and spec.source_config.exists():
        payload = spec.source_config.read_bytes(); digest = hashlib.sha256(payload).hexdigest()
        if spec.source_config_sha256 and digest != spec.source_config_sha256: raise ValueError(f'source_config_sha256_mismatch:{digest}')
        prior_model = raw.get('model') if isinstance(raw.get('model'), Mapping) else {}
        hf_config = json.loads(payload); source_text = (spec.source_config.parent.name if spec.source_config else '') + ' ' + (hf_config.get('model_type') or '') + ' ' + ' '.join(hf_config.get('architectures') or ()); source_family = _model_family(source_text); source_key = _model_key(source_text)
        prior_quant = prior_model.get('quant') if isinstance(prior_model.get('quant'), Mapping) else {}
        prior_text = str(prior_model.get('catalog_key') or (prior_quant.get('source') or {}).get('checkpoint') or ''); prior_family = _model_family(prior_text); prior_key = _model_key(prior_text)
        cross = bool(source_key and prior_key and source_key != prior_key); foreign = bool((source_family and prior_family and source_family != prior_family) or cross); same_key = bool(source_key and prior_key and source_key == prior_key)
        kept = {} if foreign else {key: prior_model[key] for key in ('quantization', 'quant', 'kv_dtype', 'metadata') if key in prior_model}
        if not foreign and kept.get('quant') is not None: normalized = _quant_dict(kept['quant']); kept['quant'] = _merge_quant_preset(kept['quant'], kept.get('quantization')); quant_data = dict(kept['quant']); provenance = dict(quant_data.get('source') or {}); provenance.pop('checkpoint', None); provenance['checkpoint_binding'] = 'not_verified_from_source'; quant_data['source'] = provenance; kept['quant'] = quant_data
        if isinstance(kept.get('quant'), (list, tuple)):
            try: kept['quant'] = dict(kept['quant'])
            except (TypeError, ValueError): kept.pop('quant', None)
        raw['model'] = {'hf_config': hf_config, **kept}; meta = dict((raw.get('runtime') or {}).get('metadata') or {}); meta['template_quant_authority'] = 'cross_version_template_rejected' if cross else ('foreign_family_rejected' if foreign else ('same_family_template_conditional' if kept else 'none')); raw.setdefault('runtime', {})['metadata'] = meta
        raw = _apply_native_quant(spec, raw)
        raw = _apply_source_cache_declaration(spec, raw, compatible=not (foreign or cross), prior_model=prior_model)
    if any((k in spec.dataset.lower() for k in ('a5', 'multinode', 'runs'))) and any((t in str(spec.model_case or '').lower() for t in ('a3', 'v4pro', 'v4f'))): raw['machine'] = json.loads((CASES_DIR / _A5_MACH_FILE).read_text(encoding='utf-8'))['machine']
    notes = tuple(dict.fromkeys(spec.notes)); nset = set(notes)
    if (hfk := next((n.split(':', 1)[1] for n in notes if n.startswith('hf_cfg:')), '')) and hfk in _MODEL_CFGS: raw['model'] = {'name': hfk, 'hf_config': _MODEL_CFGS[hfk]}; return raw
    ck = next((n.split(':', 1)[1] for n in notes if n.startswith('catalog:')), '') or (_DSPARK_KEY if 'dspark' in nset and spec.ep < 32 else '')
    if 'kv_dtype:fp8' in nset and ck: raw['model'] = {'catalog_key': ck, 'kv_dtype': 'fp8'}; return raw
    if ck or 'quant:expert_fp4' in nset:
        quant = dict(raw.get('model', {}).get('quant', {}))
        if quant and 'quant:expert_fp4' in nset: quant.update({'expert_weight_format': 'fp4_e2m1'})
        raw['model'] = {'catalog_key': ck, 'quant': quant} if 'override_model' in nset and ck else {**raw.get('model', {}), **({'catalog_key': ck} if ck else {}), **({'quant': quant} if quant else {})}
    return raw

