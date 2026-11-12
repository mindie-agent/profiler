"""Catalog base, declared downsize, and launch-matrix source match.

A template catalog_key is not a width. Matching same-run matrices or an
original config materialize the canonical model before declared depth and
expert deltas. This module does not select a grouped caller.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import fleet_archive_sources as sources

_Q30_STRUCT = {
    "hidden_size": 2048, "num_heads": 32, "num_kv_heads": 4, "head_dim": 128,
    "intermediate_size": 768, "vocab_size": 151936, "attention": "gqa", "ffn": "moe",
    "activation_dtype": "bf16", "weight_dtype": "bf16", "kv_dtype": "bf16",
    "compute_dtype": "bf16", "quantization": "none", "moe_intermediate_size": 768,
    "num_shared_experts": 0,
}

def _norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower()).replace("synth", "")


def _names_compatible(receipt: Any, *candidates: Any) -> bool:
    left = _norm_name(receipt)
    rights = [_norm_name(item) for item in candidates if _norm_name(item)]
    return bool(left) and any(left in right or right in left for right in rights)



def _model_identity(model: Mapping[str, Any]) -> dict[str, Any]:
    hf = model.get("hf_config") if isinstance(model.get("hf_config"), Mapping) else {}
    return {
        "name": model.get("name") or model.get("catalog_key") or hf.get("model_type"),
        "layers": sources.as_int(model.get("layers") if model.get("layers") is not None else hf.get("num_hidden_layers")),
        "hidden_size": sources.as_int(model.get("hidden_size") if model.get("hidden_size") is not None else hf.get("hidden_size")),
        "vocab_size": sources.as_int(model.get("vocab_size") if model.get("vocab_size") is not None else hf.get("vocab_size")),
        "num_experts": sources.as_int(model.get("num_experts") if model.get("num_experts") is not None else (hf.get("n_routed_experts") if hf.get("n_routed_experts") is not None else hf.get("num_experts"))),
        "top_k": sources.as_int(model.get("top_k") if model.get("top_k") is not None else hf.get("num_experts_per_tok")),
    }


def _json_data(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_data(item) for item in value]
    if isinstance(value, list):
        return [_json_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_data(item) for key, item in value.items()}
    return value


def _original_config(source_path: Path | None) -> dict[str, Any] | None:
    if not isinstance(source_path, Path):
        return None
    path = source_path.parent / "config.json"
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > 2_000_000:
            return None
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    text = document.get("text_config") if isinstance(document.get("text_config"), dict) else document
    return text if isinstance(text, dict) else None


def _config_int(config: Mapping[str, Any] | None, *keys: str) -> int | None:
    if not isinstance(config, Mapping):
        return None
    for key in keys:
        if key in config:
            return sources.as_int(config.get(key))
    return None


def _class_signatures(spec: Any) -> dict[str, dict[str, int]] | str:
    grouped: dict[str, list] = {}
    for plan in spec.layer_plans:
        grouped.setdefault(str(plan.attention), []).append(plan)
    signatures: dict[str, dict[str, int]] = {}
    for attention, plans in grouped.items():
        fields = ("num_heads", "num_kv_heads", "head_dim", "num_experts", "top_k", "moe_intermediate_size", "linear_heads", "linear_head_dim")
        first = {field: int(getattr(plans[0], field)) for field in fields}
        if any(int(getattr(plan, field)) != first[field] for plan in plans for field in fields):
            return f"catalog_layer_class_heterogeneous:{attention}"
        signatures[attention] = {"count": len(plans), **first}
    return signatures


def _refuse_widths(witness: Mapping[str, Any], catalog_hidden: int, catalog_intermediate: int,
                   full_local: int, linear_dims: set[int]) -> tuple[int, int, str] | tuple[None, None, str]:
    """Match one hidden and one MoE intermediate. Extra projection widths may remain."""
    matmul = [(int(item[0]), int(item[1])) for item in (witness.get("matmul_kn") or []) if isinstance(item, list) and len(item) == 2]
    grouped = [(int(item[0]), int(item[1])) for item in (witness.get("grouped_kn") or []) if isinstance(item, list) and len(item) == 2]
    if not matmul and not grouped and not witness.get("expert_axes") and not witness.get("permute_widths"):
        return None, None, "launch_matrix_widths_absent"
    hidden_candidates = sorted({k for k, _n in matmul} & {n for _k, n in matmul})
    permute = [int(item) for item in (witness.get("permute_widths") or [])]
    if permute:
        hidden_candidates = sorted(set(hidden_candidates) & set(permute)) if hidden_candidates else sorted(set(permute))
    if len(hidden_candidates) != 1:
        if not hidden_candidates:
            return None, None, "launch_matrix_widths_absent"
        return None, None, "launch_hidden_width_ambiguous:" + ",".join(str(item) for item in hidden_candidates)
    hidden = hidden_candidates[0]
    if hidden != catalog_hidden:
        return None, None, f"catalog_width_disagrees_with_launch_matrices:hidden:witness={hidden}:catalog={catalog_hidden}"
    intermediates = sorted({k for k, n in grouped if n == hidden and k != hidden and k > 0})
    if len(intermediates) != 1:
        if not intermediates:
            return None, None, "launch_matrix_widths_absent"
        return None, None, "catalog_width_disagrees_with_launch_matrices:moe_intermediate:" + ",".join(str(item) for item in intermediates)
    intermediate = intermediates[0]
    if intermediate != catalog_intermediate:
        return None, None, f"catalog_width_disagrees_with_launch_matrices:moe_intermediate:witness={intermediate}:catalog={catalog_intermediate}"
    local = {k for k, n in matmul if n == hidden and 0 < k < hidden}
    if full_local not in local:
        return None, None, f"catalog_head_width_disagrees_with_launch_matrices:local={full_local}:seen=" + ",".join(str(item) for item in sorted(local))
    missing_linear = sorted(dim for dim in linear_dims if dim not in local)
    if missing_linear:
        return None, None, "catalog_width_disagrees_with_launch_matrices:linear_head_dim:" + ",".join(str(item) for item in missing_linear)
    return hidden, intermediate, "launch_matrices"


def _materialize_catalog_full(template: Mapping[str, Any], declaration: Mapping[str, Any], *,
                              catalog_key: str, layers: int | None, experts: int | None,
                              top_k: int | None, base: Any) -> tuple[dict | None, list[str], list[str]]:
    """Expand a full-size catalog model without inventing widths or downsizing."""
    from mindie_sim.model_catalog import customize_model_spec
    from mindie_sim.schema.common import ModelingError
    from mindie_sim.schema.serialization import apply_model_overrides

    notes = ["catalog_full_size_materialized_before_runtime_overrides"]
    receipt_hidden = sources.as_int(declaration.get("hidden_size"))
    receipt_vocab = sources.as_int(declaration.get("vocab_size"))
    if receipt_hidden is not None and receipt_hidden != base.hidden_size:
        return None, [f"hidden_size_disagrees:receipt={receipt_hidden}:catalog={base.hidden_size}"], ["hidden_size"]
    if receipt_vocab is not None and receipt_vocab != base.vocab_size:
        return None, [f"vocab_size_disagrees:receipt={receipt_vocab}:catalog={base.vocab_size}"], ["vocab_size"]
    chosen_layers = layers if isinstance(layers, int) else int(base.layers)
    chosen_experts = experts if isinstance(experts, int) else int(base.num_experts)
    chosen_topk = top_k if isinstance(top_k, int) else int(base.top_k)
    if chosen_layers != int(base.layers) or chosen_experts != int(base.num_experts) or chosen_topk != int(base.top_k):
        return None, ["catalog_full_size_delta_is_not_a_downsize"], ["model identity"]
    try:
        adjustments = {}
        if chosen_layers != int(base.layers):
            adjustments["layers"] = chosen_layers
        if chosen_experts != int(base.num_experts) or chosen_topk != int(base.top_k):
            adjustments["n_routed_experts"] = chosen_experts
            adjustments["num_experts_per_tok"] = chosen_topk
        spec = customize_model_spec(base, **adjustments) if adjustments else base
        raw_override = {}
        if template.get("quantization") not in (None, ""):
            raw_override["quantization"] = template.get("quantization")
        if isinstance(template.get("quant"), dict):
            raw_override["quant"] = template.get("quant")
        if raw_override:
            spec = apply_model_overrides(spec, raw_override)
    except ModelingError as exc:
        return None, [str(exc)], ["model"]
    data = _json_data(spec.to_dict())
    data.pop("catalog_key", None)
    data.pop("model_catalog_key", None)
    data.pop("preset", None)
    metadata = dict(data.get("metadata") or {})
    metadata.update({
        "architectural_basis": "catalog_full_size",
        "catalog_key": str(catalog_key),
        "depth_basis": "catalog_model",
        "not_full_catalog_depth": False,
        "expert_basis": "catalog",
        "not_full_catalog_experts": False,
        "top_k_basis": "catalog",
        "source_layers": int(spec.layers),
        "source_num_experts": int(spec.num_experts),
        "source_top_k": int(spec.top_k),
        "source_hidden_size": int(spec.hidden_size),
        "source_vocab_size": int(spec.vocab_size),
        "runtime_overrides": sorted(raw_override),
    })
    data["metadata"] = metadata
    return data, notes, []


def _materialize_catalog_downsize(template: Mapping[str, Any], declaration: Mapping[str, Any], *,
                                  catalog_key: str, layers: int, experts: int, top_k: int,
                                  source_path: Path | None, parallel: Mapping[str, Any] | None,
                                  base: Any) -> tuple[dict | None, list[str], list[str]]:
    from mindie_sim.model_catalog import customize_model_spec
    from mindie_sim.schema.common import ModelingError
    from mindie_sim.schema.serialization import apply_model_overrides

    from fleet_archive_producer_reader import witness_launch_matrices

    notes: list[str] = ["catalog_base_materialized_before_declared_deltas"]
    receipt_hidden = sources.as_int(declaration.get("hidden_size"))
    receipt_vocab = sources.as_int(declaration.get("vocab_size"))
    if receipt_hidden is not None and receipt_hidden != base.hidden_size:
        return None, [f"hidden_size_disagrees:receipt={receipt_hidden}:catalog={base.hidden_size}"], ["hidden_size"]
    if receipt_vocab is not None and receipt_vocab != base.vocab_size:
        return None, [f"vocab_size_disagrees:receipt={receipt_vocab}:catalog={base.vocab_size}"], ["vocab_size"]
    config = _original_config(source_path)
    config_hidden = _config_int(config, "hidden_size")
    config_heads = _config_int(config, "num_attention_heads", "num_heads")
    config_head_dim = _config_int(config, "head_dim")
    config_intermediate = _config_int(config, "moe_intermediate_size")
    config_experts = _config_int(config, "num_experts", "n_routed_experts")
    config_topk = _config_int(config, "num_experts_per_tok", "top_k")
    if config_hidden is not None and config_hidden != base.hidden_size:
        return None, [f"hidden_size_disagrees:original_config={config_hidden}:catalog={base.hidden_size}"], ["hidden_size"]
    if config_heads is not None and config_heads != base.num_heads:
        return None, [f"catalog_width_disagrees_with_original_config:num_heads:config={config_heads}:catalog={base.num_heads}"], ["num_heads"]
    if config_head_dim is not None and config_head_dim != base.head_dim:
        return None, [f"catalog_width_disagrees_with_original_config:head_dim:config={config_head_dim}:catalog={base.head_dim}"], ["head_dim"]
    if config_intermediate is not None and config_intermediate != base.moe_intermediate_size:
        return None, [f"catalog_width_disagrees_with_original_config:moe_intermediate:config={config_intermediate}:catalog={base.moe_intermediate_size}"], ["moe_intermediate_size"]
    if config_experts is not None and config_experts != experts:
        return None, [f"original_config_routed_dims_disagree_with_declaration:experts:config={config_experts}:declared={experts}"], ["num_experts"]
    if config_topk is not None and config_topk != top_k:
        return None, [f"original_config_routed_dims_disagree_with_declaration:top_k:config={config_topk}:declared={top_k}"], ["top_k"]
    tp = sources.as_int((parallel or {}).get("tp")) if isinstance(parallel, Mapping) else None
    ep = sources.as_int((parallel or {}).get("ep")) if isinstance(parallel, Mapping) else None
    if not isinstance(tp, int) or tp < 1 or (base.num_heads * base.head_dim) % tp != 0:
        return None, [f"catalog_head_width_disagrees_with_launch_matrices:tp={tp}"], ["tp"]
    full_local = (base.num_heads * base.head_dim) // tp
    try:
        spec = customize_model_spec(base, layers=layers, n_routed_experts=experts, num_experts_per_tok=top_k)
    except ModelingError as exc:
        return None, [str(exc)], ["model.layers"]
    signatures = _class_signatures(spec)
    if isinstance(signatures, str):
        return None, [signatures], ["model.layer_plans"]
    linear_dims = {int(item["linear_head_dim"]) for item in signatures.values() if int(item.get("linear_head_dim") or 0) > 0}
    witness = witness_launch_matrices(source_path) if isinstance(source_path, Path) else {
        "opened": False, "rows_seen": 0, "capped": False, "matmul_kn": [], "grouped_kn": [],
        "expert_axes": [], "topk_axes": [], "gating_topk": [], "permute_widths": [],
    }
    hidden, intermediate, width_source = _refuse_widths(witness, base.hidden_size, base.moe_intermediate_size, full_local, linear_dims)
    config_covers = config_hidden == base.hidden_size and config_heads == base.num_heads and config_head_dim == base.head_dim and config_intermediate == base.moe_intermediate_size
    if hidden is None:
        if width_source == "launch_matrix_widths_absent" and config_covers:
            hidden = base.hidden_size
            intermediate = base.moe_intermediate_size
            width_source = "original_config"
        else:
            return None, [width_source], ["model.hidden_size"]
    elif config_covers:
        width_source = "original_config_and_launch_matrices"
    expert_axes = [int(item) for item in (witness.get("expert_axes") or [])]
    permute_topk = [int(item) for item in (witness.get("topk_axes") or [])]
    gating_topk = [int(item) for item in (witness.get("gating_topk") or [])]
    if permute_topk and gating_topk and permute_topk != gating_topk:
        return None, [f"launch_topk_sources_disagree:permute={','.join(str(item) for item in permute_topk)}:gating={','.join(str(item) for item in gating_topk)}"], ["model.top_k"]
    topk_axes = permute_topk or gating_topk
    if expert_axes or topk_axes:
        if not expert_axes or not topk_axes:
            return None, ["launch_matrix_widths_absent"], ["model.num_experts", "model.top_k"]
        if expert_axes != [experts]:
            witnessed = ",".join(str(item) for item in expert_axes)
            return None, [f"launch_routed_dims_disagree_with_declaration:experts:witness={witnessed}:declared={experts}"], ["num_experts"]
        if topk_axes != [top_k]:
            witnessed = ",".join(str(item) for item in topk_axes)
            return None, [f"launch_routed_dims_disagree_with_declaration:top_k:witness={witnessed}:declared={top_k}"], ["top_k"]
    elif config_experts != experts or config_topk != top_k:
        return None, ["launch_matrix_widths_absent"], ["model.num_experts", "model.top_k"]
    raw_override = {}
    if template.get("quantization") not in (None, ""):
        raw_override["quantization"] = template.get("quantization")
    if isinstance(template.get("quant"), dict):
        raw_override["quant"] = template.get("quant")
    try:
        if raw_override:
            spec = apply_model_overrides(spec, raw_override)
    except ModelingError as exc:
        return None, [str(exc)], ["model.quantization"]
    data = _json_data(spec.to_dict())
    data.pop("catalog_key", None)
    data.pop("model_catalog_key", None)
    data.pop("preset", None)
    if isinstance(declaration.get("name"), str) and declaration["name"].strip():
        data["name"] = declaration["name"]
    metadata = dict(data.get("metadata") or {})
    metadata.update({
        "architectural_basis": "catalog_base_then_declared_downsize",
        "catalog_key": str(catalog_key),
        "depth_basis": "receipt_model_declaration",
        "not_full_catalog_depth": layers < int(base.layers),
        "expert_basis": "registry_and_path" if experts != int(base.num_experts) else "catalog",
        "not_full_catalog_experts": experts != int(base.num_experts),
        "top_k_basis": "registry_and_path" if top_k != int(base.top_k) else "catalog",
        "source_match": width_source,
        "source_hidden_size": int(hidden),
        "source_moe_intermediate_size": int(intermediate),
        "source_intermediate_size": int(spec.intermediate_size),
        "source_num_heads": int(spec.num_heads),
        "source_head_dim": int(spec.head_dim),
        "source_num_kv_heads": int(spec.num_kv_heads),
        "source_layers": layers,
        "source_num_experts": experts,
        "source_top_k": top_k,
        "source_tp": tp,
        "source_ep": ep,
        "source_vocab_size": int(spec.vocab_size),
        "class_signatures": signatures,
        "witness_rows_seen": int(witness.get("rows_seen") or 0),
        "witness_capped": bool(witness.get("capped")),
    })
    data["metadata"] = metadata
    if layers != int(base.layers):
        notes.append("model_layers_taken_from_receipt")
    if experts != int(base.num_experts):
        notes.append("model_experts_taken_from_registry_and_path")
    if top_k != int(base.top_k):
        notes.append("model_topk_taken_from_registry_and_path")
    notes.append(f"source_match:{width_source}")
    if witness.get("capped"):
        notes.append(f"launch_matrix_witness_capped_at_{witness.get('rows_seen')}")
    return data, notes, []


def _reconcile_model(case_doc, declaration, family, tokens, registry_layers, registry_experts, registry_top_k,
                     source_path=None, parallel=None):
    notes: list[str] = []
    missing: list[str] = []
    if str(family or "").startswith("synth-qwen3-30b") or str(family or "") == "qwen3-30b-a3b":
        hidden = sources.as_int(declaration.get("hidden_size"))
        vocab = sources.as_int(declaration.get("vocab_size"))
        case_model = case_doc.get("model") if isinstance(case_doc, Mapping) and isinstance(case_doc.get("model"), Mapping) else {}
        if hidden is None or vocab is None:
            identity = _model_identity(case_model) if case_model else {}
            if hidden is None:
                hidden = sources.as_int(identity.get("hidden_size"))
            if vocab is None:
                vocab = sources.as_int(identity.get("vocab_size"))
            if hidden is not None or vocab is not None:
                notes.append("qwen30_widths_from_original_case_after_receipt_omission")
        if hidden != _Q30_STRUCT["hidden_size"] or vocab != _Q30_STRUCT["vocab_size"]:
            return None, ["qwen30_receipt_identity_disagrees_with_generator_skeleton"], ["model.hidden_size", "model.vocab_size"]
        label = declaration.get("name")
        placeholder = label in (None, "", "model")
        if not placeholder and not _names_compatible(label, "qwen3-30b-a3b", family):
            return None, [f"model_name_disagrees:{label}"], ["model.name"]
        if placeholder:
            notes.append("receipt_model_name_not_specific")
        layers = _agree_int("layers", declaration.get("layers"), registry_layers, tokens.get("layers"))
        experts = _agree_int("num_experts", None, registry_experts, tokens.get("num_experts"))
        top_k = _agree_int("top_k", None, registry_top_k, tokens.get("top_k"))
        if isinstance(layers, str) or isinstance(experts, str) or isinstance(top_k, str):
            return None, [item for item in (layers, experts, top_k) if isinstance(item, str)], ["model.layers"]
        if layers is None or experts is None or top_k is None:
            return None, ["qwen30_layers_experts_topk_incomplete"], ["model.layers", "model.num_experts", "model.top_k"]
        model = {"name": str(family if placeholder else label), "layers": layers, "num_experts": experts, "top_k": top_k, **_Q30_STRUCT}
        model["metadata"] = {"depth_basis": "receipt_model_declaration", "structural_basis": "a5_resolve_template_explicit_model"}
        return model, notes, missing
    if not isinstance(case_doc, Mapping) or not isinstance(case_doc.get("model"), Mapping):
        return None, ["original_case_has_no_model"], ["model"]
    identity = _model_identity(case_doc["model"])
    if declaration.get("name") not in (None, ""):
        if not _names_compatible(declaration.get("name"), identity.get("name"), family, case_doc.get("name")):
            return None, [f"model_name_disagrees:receipt={declaration.get('name')}:case={identity.get('name')}"], ["matching model declaration"]
    else:
        notes.append("receipt_model_name_absent")
    for key, receipt_key in (("hidden_size", "hidden_size"), ("vocab_size", "vocab_size")):
        if declaration.get(receipt_key) is not None and identity.get(key) is not None and sources.as_int(declaration.get(receipt_key)) != identity.get(key):
            return None, [f"{key}_disagrees:receipt={declaration.get(receipt_key)}:case={identity.get(key)}"], [key]
    layers = _agree_int("layers", declaration.get("layers"), registry_layers, tokens.get("layers"))
    experts = _agree_int("num_experts", registry_experts, tokens.get("num_experts"))
    top_k = _agree_int("top_k", registry_top_k, tokens.get("top_k"))
    conflicts = [item for item in (layers, experts, top_k) if isinstance(item, str)]
    if conflicts:
        return None, conflicts, ["model identity agreement"]
    template_model = case_doc["model"]
    catalog_key = template_model.get("catalog_key") or template_model.get("model_catalog_key")
    if isinstance(catalog_key, str) and catalog_key.strip():
        from mindie_sim.model_catalog import load_model
        from mindie_sim.schema.common import ModelingError

        try:
            base = load_model(catalog_key.strip())
        except ModelingError as exc:
            return None, [str(exc)], ["model.catalog_key"]
        declared_layers = layers if isinstance(layers, int) else None
        declared_experts = experts if isinstance(experts, int) else None
        declared_topk = top_k if isinstance(top_k, int) else None
        depth_down = declared_layers is not None and declared_layers < int(base.layers)
        depth_over = declared_layers is not None and declared_layers > int(base.layers)
        expert_delta = declared_experts is not None and declared_experts != int(base.num_experts)
        topk_delta = declared_topk is not None and declared_topk != int(base.top_k)
        if depth_over:
            return None, [f"declared_layers_exceed_catalog:{declared_layers}>{base.layers}"], ["model.layers"]
        if depth_down or expert_delta or topk_delta:
            if declared_layers is None or declared_experts is None or declared_topk is None:
                absent = [name for name, value in (
                    ("model.layers", declared_layers), ("model.num_experts", declared_experts), ("model.top_k", declared_topk),
                ) if value is None]
                return None, ["catalog_downsize_declaration_incomplete"], absent
            materialized, down_notes, down_missing = _materialize_catalog_downsize(
                template_model, declaration, catalog_key=catalog_key.strip(), layers=declared_layers,
                experts=declared_experts, top_k=declared_topk, source_path=source_path, parallel=parallel, base=base,
            )
            notes.extend(down_notes)
            return materialized, notes, down_missing
        materialized, full_notes, full_missing = _materialize_catalog_full(
            template_model, declaration, catalog_key=catalog_key.strip(), layers=declared_layers,
            experts=declared_experts, top_k=declared_topk, base=base,
        )
        notes.extend(full_notes)
        return materialized, notes, full_missing
    model = json.loads(json.dumps(template_model))
    model.pop("catalog_key", None)
    model.pop("model_catalog_key", None)
    if isinstance(layers, int) and layers != identity.get("layers"):
        model["layers"] = layers
        hf = model.get("hf_config")
        if isinstance(hf, dict):
            hf["num_hidden_layers"] = layers
        notes.append("model_layers_taken_from_receipt")
        model.setdefault("metadata", {})
        if isinstance(model["metadata"], dict):
            model["metadata"]["depth_basis"] = "receipt_model_declaration"
            model["metadata"]["not_full_catalog_depth"] = True
    if isinstance(experts, int):
        model["num_experts"] = experts
        hf = model.get("hf_config")
        if isinstance(hf, dict) and "n_routed_experts" in hf:
            hf["n_routed_experts"] = experts
        if experts != identity.get("num_experts"):
            notes.append("model_experts_taken_from_registry_and_path")
            model.setdefault("metadata", {})
            if isinstance(model["metadata"], dict):
                model["metadata"]["expert_basis"] = "registry_and_path"
                model["metadata"]["not_full_catalog_experts"] = True
    elif identity.get("num_experts") is None:
        missing.append("num_experts")
    if isinstance(top_k, int):
        model["top_k"] = top_k
        hf = model.get("hf_config")
        if isinstance(hf, dict) and "num_experts_per_tok" in hf:
            hf["num_experts_per_tok"] = top_k
        if top_k != identity.get("top_k"):
            notes.append("model_topk_taken_from_registry_and_path")
            model.setdefault("metadata", {})
            if isinstance(model["metadata"], dict):
                model["metadata"]["top_k_basis"] = "registry_and_path"
    elif identity.get("top_k") is None:
        missing.append("top_k")
    if isinstance(declaration.get("name"), str):
        model["name"] = declaration["name"]
    return model, notes, missing


def _agree_int(label: str, *values: Any) -> int | str | None:
    present = [value for value in (sources.as_int(item) for item in values) if value is not None]
    if not present:
        return None
    if len(set(present)) != 1:
        return f"conflict:{label}:" + ",".join(str(item) for item in present)
    return present[0]


