"""Independent case and source choices for retained profiling replay.

[Role] Select explicit declarations without reading observed kernel descriptors.
[Invariants] Source-selected variants retain provenance and never become defaults.
  Historical observations do not identify checkpoint precision or native dispatch.
[Timeouts & Locks] Bounded metadata only, no device calls, network or locks.
[Side-Effect Policy] Reads local case/evidence JSON; creates in-memory declarations.
"""
from hashlib import sha256
from copy import deepcopy
import json
from pathlib import Path


def _read(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError(f"metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


def _hash(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _variant(key, old, base, *, decode=False, fused=False, checkpoint=False):
    import mindie_sim

    execution = {name: old["declared_execution"][name]
                 for name in ("phase", "tokens", "context", "sequences")}
    if decode:
        execution.update(phase="decode", tokens=1, context=32768)
    historical_case = Path(old["declaration_source"]["case_path"])
    # A replay checkout owns its declarations as well as its imported runtime;
    # the capture receipt's original checkout may still be under development.
    case_path = (Path(mindie_sim.__file__).resolve().parents[1]
                 / "examples/cases" / historical_case.name)
    source_program_evidence = None
    if fused and "glm53" in key:
        case_path = (case_path.parents[2] / "data/verification"
                     / "model-scoreboard-20261029-glm53-w4a8-msd-case.json")
        source_program_evidence = {
            "basis": "independent_source_program_and_balanced_routing_scenario",
            "path": str(case_path), "sha256": _hash(case_path),
            "routing_values_observed": False,
            "capture_dispatch_identity_verified": False,
        }
    checkpoint_evidence = None
    if checkpoint:
        case_path = case_path.with_name("kimi-k3-a5-current-checkpoint-conditional.json")
        evidence_root = case_path.parents[2] / "data/observations/sources/kimi-checkpoint-20261029"
        checkpoint_evidence = {
            "basis": "independent_current_checkpoint_metadata",
            "historical_config_hash_matches": True,
            "historical_quantization_hash_available": False,
            "capture_dispatch_identity_verified": False,
            "files": [{"path": str(path), "sha256": _hash(path)}
                      for path in sorted(evidence_root.glob("*.json"))],
        }
        if not checkpoint_evidence["files"]:
            raise ValueError("kimi_checkpoint_evidence_missing")
    case = _read(case_path)
    lowerings = {}
    passes = None
    norm_evidence = None
    if "glm53" in key or decode:
        lowerings["mla_prolog"] = "vllm_ascend_mla_prolog_v3"
    if checkpoint:
        lowerings.update({
            "mla_prolog": "vllm_ascend_mla_prolog_v3",
            "rmsnorm_quant": {
                "implementation": "vllm_ascend_native_norm",
                "options": {"has_bias": False},
            },
            "native_fusion": {
                "implementation": "declared_native_fusion",
                "options": {
                    "roles": ["situ_quant", "grouped_gate_up_situ_quant"],
                    "traffic_profile": {
                        "situ_quant": "situ_mx_quant_arch35_2a9bd1b0",
                        "grouped_gate_up_situ_quant": "preserve_workspaces",
                    },
                },
            },
        })
        passes = ["activation_quantization", "norm_quant"]
        case.setdefault("runtime", {})["lowering_passes"] = passes
    if "glm53" in key:
        evidence_path = base / "head-normalization-evidence.json"
        evidence = _read(evidence_path)
        selection = evidence["selected_glm_scenario"]
        lowerings.update(selection["kernels"]["lowerings"])
        passes = selection["lowering_passes"]
        case.setdefault("runtime", {})["lowering_passes"] = passes
        norm_evidence = {
            "file": str(evidence_path), "sha256": _hash(evidence_path),
            "basis": "independent_checkpoint_global_norm_bias_predicate_and_source",
            "checkpoint_metadata_sha256": evidence["glm_checkpoint"]["sha256"],
            "source_sha256": evidence["glm_runtime_source"]["sha256"],
            "capture_dispatch_identity_verified": False,
        }
    if fused:
        if "glm53" in key:
            options = dict(case["runtime"]["kernels"]["lowerings"]["native_fusion"]["options"])
            options["roles"] = list(dict.fromkeys([
                *options["roles"], "mla_prolog", "lightning_indexer"]))
            options["traffic_profile"] = "preserve_workspaces"
        else:
            options = {"roles": ["hc_pre", "hc_post"], "traffic_profile": {
                "hc_pre": "hc_pre_m_k_split_175ef4d4",
                "hc_post": "hc_post_d_split_175ef4d4"}}
        lowerings["native_fusion"] = {
            "implementation": "declared_native_fusion", "options": options}
    case.setdefault("runtime", {}).setdefault("kernels", {}).setdefault("lowerings", {}).update(
        lowerings)
    base_key = key + ("_decode" if decode else "") + ("_checkpoint" if checkpoint else "")
    name = base_key + ("-selected" if fused else "-reference")
    return {
        "name": name, "declaration_key": base_key, "case": case, "geometry": execution,
        "variant": ("current_checkpoint_conditional" if checkpoint else
                    "selected_native_fusion" if fused else
                    "source_declared_unfused_reference" if lowerings else "case_default"),
        "declaration_source": {
            "case_path": str(case_path), "case_sha256": _hash(case_path),
            "historical_case_path": str(historical_case),
            "implementation_overrides": lowerings,
            "lowering_passes_override": passes,
            "override_basis": "caller_declared_source_selection",
            "capture_dispatch_identity_verified": False,
            "source_evidence": {
                "mla_prolog": "prediction/family_mla_prolog.py selected source declaration",
                "resource_reuse": "fusion_boundary.evidence in exported structure",
                "native_norm": norm_evidence,
                "current_checkpoint": checkpoint_evidence,
                "source_program": source_program_evidence,
            } if lowerings else None,
        },
    }


def _compressor_fp32_variant(key, old, base):
    """Choose independently documented norm precision without claiming dispatch."""
    from mindie_sim.prediction.structure import parse_case

    variant = _variant(key, old, base, fused=True)
    case = variant["case"]
    evidence_path = base / "compressor-normalization-evidence.json"
    evidence = _read(evidence_path)
    plans = parse_case(case).model.layer_plans
    overrides = case["model"].setdefault("layer_overrides", {})
    selected = {}
    for plan in plans:
        if plan.compressor_kind != "none" and plan.compress_ratio > 1:
            change = {"compressor_norm_dtype": evidence["selection"]["compressor_norm_dtype"]}
            overrides.setdefault(str(plan.index), {}).update(change)
            selected[str(plan.index)] = change
    variant.update(
        name=key + "_compressor_fp32-reference",
        declaration_key=key + "_compressor_fp32",
        variant="source_compressor_fp32_conditional_reference",
    )
    source = variant["declaration_source"]
    source["model_layer_overrides"] = selected
    source["source_evidence"]["compressor_norm"] = {
        "file": str(evidence_path), "sha256": _hash(evidence_path),
        "basis": "independent_runtime_source_parameter_precision",
        "source_revision": evidence["norm_source"]["revision"],
        "source_sha256": evidence["norm_source"]["sha256"],
        "capture_dispatch_identity_verified": False,
        "historical_capture_source_revision_verified": False,
        "resource_boundary": "unfused_semantic_reference",
        "single_launch_selection": False,
        "limitations": evidence["resource_coverage"]["limitations"],
    }
    return variant


def _steady_matmul_variant(key, old, base):
    variant = _variant(key, old, base)
    source = variant["declaration_source"]
    case_path = (Path(source["case_path"]).parents[2] / "data/verification"
                 / "matrix-cohort-wave4-20261029/a5_qwen38-steady.case.json")
    variant.update(
        name=key + "_steady-selected", declaration_key=key + "_steady",
        variant="selected_steady_matrix_conditional", case=_read(case_path),
    )
    source.update(
        case_path=str(case_path), case_sha256=_hash(case_path),
        override_basis="explicit_source_recipe_selection",
        source_evidence={
            "steady_matrix": {
                "source_commit": "ea0bae98",
                "case_path": str(case_path), "case_sha256": _hash(case_path),
                "program": "steady_matmul",
                "capture_dispatch_identity_verified": False,
                "replaces_reference_variant": False,
            },
        },
    )
    return variant


def _shared_quant_variant(key, old, base):
    variant = _variant(key, old, base)
    source = variant["declaration_source"]
    source_key = "a3_glm53_prefill" if key == "a3_glm53_decode" else key
    case_path = (Path(source["case_path"]).parents[2] / "data/verification"
                 / "shared-quant-wave4-20261029" / f"{source_key}.case.json")
    variant.update(
        name=key + "_shared_quant-selected", declaration_key=key + "_shared_quant",
        variant="source_shared_int32_conditional", case=_read(case_path),
    )
    source.update(
        case_path=str(case_path), case_sha256=_hash(case_path),
        implementation_overrides=variant["case"]["runtime"]["kernels"]["lowerings"],
        lowering_passes_override=variant["case"]["runtime"].get("lowering_passes"),
        override_basis="independent_source_separate_int32_producer_and_dequant_consumer",
        source_evidence={
            "shared_quant": {
                "source_commit": "0ad29aa3",
                "case_path": str(case_path), "case_sha256": _hash(case_path),
                "implementation": "ascend_shared_gate_up_int32",
                "geometry_basis": "existing_independent_capture_phase_declaration",
                "capture_dispatch_identity_verified": False,
                "replaces_reference_variant": False,
            },
        },
    )
    return variant


def _kimi_single_group_variant(key, old, base, *, decode):
    variant = _variant(key, old, base, decode=decode, checkpoint=True)
    case, source = variant["case"], variant["declaration_source"]
    selection = {
        "implementation": "vllm_ascend_mxfp8_single_group_eager",
        "options": {"projection_recipes": ["latent_projection"]},
    }
    case["runtime"]["graph_mode"] = "eager"
    case["runtime"]["kernels"]["lowerings"]["matrix_wrapper"] = selection
    source["implementation_overrides"]["matrix_wrapper"] = selection
    source["runtime_overrides"] = {"graph_mode": "eager"}
    evidence_path = (base.parents[2] / "tests/fixtures/kimi_grouped_attnres"
                     / "source_image_883670fc/provenance.json")
    source["source_evidence"]["single_group_wrapper"] = {
        "file": str(evidence_path), "sha256": _hash(evidence_path),
        "implementation": selection["implementation"],
        "caller_domain": ["latent_projection"],
        "group_list_source": "wrapper_sets_one_group_covering_all_input_rows",
        "source_image": "sha256:883670fcc91cbd75a7070b00501be0ecd81a266b81366a21bf02139d8e6a33e1",
        "captured_eager_dispatch_verified": False,
        "excluded_source_callers": ["unrepresented_fused_kda_qkv"],
        "excluded_matrix_domains": ["routed_expert_banks"],
    }
    declaration = variant["declaration_key"] + "_eager_single_group"
    variant.update(
        name=declaration + "-reference", declaration_key=declaration,
        variant="source_single_group_mxfp8_conditional",
    )
    return variant


def _kimi_sp_variant(key, old, base):
    variant = _kimi_single_group_variant(key, old, base, decode=False)
    source = variant["declaration_source"]
    case_path = Path(source["case_path"]).with_name(
        "kimi-k3-a5-sequence-parallel-conditional.json")
    case = _read(case_path)
    evidence = source["source_evidence"]
    source.update(
        case_path=str(case_path), case_sha256=_hash(case_path),
        implementation_overrides=case["runtime"]["kernels"].get("lowerings", {}),
        lowering_passes_override=case["runtime"].get("lowering_passes"),
        runtime_overrides={
            "graph_mode": case["runtime"]["graph_mode"],
            "kernels.sequence_parallel": case["runtime"]["kernels"]["sequence_parallel"],
        },
        source_evidence={
            "current_checkpoint": evidence["current_checkpoint"],
            "single_group_wrapper": evidence["single_group_wrapper"],
            "sequence_parallel": {
                "source_commit": "1aeb52ad",
                "case_path": str(case_path), "case_sha256": _hash(case_path),
                "global_token_basis": "per_data_parallel_replica",
                "local_row_basis": "independently_declared_global_tokens_divided_by_tp",
                "expert_pool_basis": "complete_data_parallel_expert_cohort",
                "padding": "none",
                "small_m_decode_padding_supported": False,
                "capture_dispatch_identity_verified": False,
            },
        },
    )
    declaration = variant["declaration_key"] + "_sp"
    variant.update(
        name=declaration + "-selected", declaration_key=declaration, case=case,
        variant="source_sp_single_group_mxfp8_conditional",
    )
    return variant


def _staged_paged_variants(key, values):
    from copy import deepcopy

    if key != "a5_qwen38":
        return []
    result = []
    for original in values:
        if (original["variant"] != "paged_body_geometry_conditional"
                or original["geometry"]["phase"] != "decode"):
            continue
        value = deepcopy(original)
        source = value["declaration_source"]
        sim = Path(source["case_path"]).parents[2]
        case_path = sim / "examples/source-families/paged-fia-a5-decode.json"
        evidence_path = sim / "data/verification/paged-fia-selection-20261029.json"
        case = _read(case_path)
        declaration = value["declaration_key"] + "_staged"
        value.update(
            name=declaration + "-selected", declaration_key=declaration, case=case,
            variant="source_paged_decode_program_conditional",
        )
        source.update(
            case_path=str(case_path), case_sha256=_hash(case_path),
            runtime_overrides={
                "attention_policy": case["runtime"]["attention_policy"],
                "kernels.recipes": case["runtime"]["kernels"]["recipes"],
            },
        )
        source["source_evidence"]["paged_attention_program"] = {
            "source_commit": "fb66e7d5",
            "case_path": str(case_path), "case_sha256": _hash(case_path),
            "paired_evidence_path": str(evidence_path),
            "paired_evidence_sha256": _hash(evidence_path),
            "program": "staged_gqa_decode",
            "basis": "explicit_source_recipe_selection; measured_durations_not_used_as_model_input",
            "capture_dispatch_identity_verified": False,
            "applies_to_architecture": "A5",
        }
        result.append(value)
    return result


def _combined_prefill_variants(key, values):
    """Compose independent recipes while keeping each storage ABI explicit."""
    if key not in {"a3_qwen35", "a3_qwen36", "a5_qwen38"}:
        return []
    paged = next(value for value in values
                 if value["variant"] == "paged_body_geometry_conditional"
                 and value["geometry"]["phase"] == "prefill")
    originals = [paged]
    if key == "a5_qwen38":
        originals.append(values[0])
    result = []
    for original in originals:
        value = deepcopy(original)
        source = value["declaration_source"]
        sim = Path(source["case_path"]).parents[2]
        # These controls declare one portable staged recipe. Only that recipe
        # is copied; machine, model, storage and other programs stay in the arm.
        recipe_case = sim / "examples/source-families" / (
            "paged-fia-a3-prefill-qwen36.json" if key == "a3_qwen36"
            else "paged-fia-a3-prefill-qwen35.json")
        recipe = _read(recipe_case)["runtime"]["kernels"]["recipes"]["flash_attention_prefill"]
        runtime = value["case"].setdefault("runtime", {})
        kernels = runtime.setdefault("kernels", {})
        kernels.setdefault("recipes", {})["flash_attention_prefill"] = deepcopy(recipe)
        storage = "paged" if original is paged else "contiguous"
        policy = "paged" if original is paged else "auto"
        runtime.setdefault("attention_policy", {})["kv_storage"] = policy
        overrides = source.setdefault("runtime_overrides", {})
        overrides["attention_policy"] = deepcopy(runtime["attention_policy"])
        overrides["kernels.recipes.flash_attention_prefill"] = deepcopy(recipe)
        evidence = source.setdefault("source_evidence", {}) or {}
        source["source_evidence"] = evidence
        evidence_path = sim / "data/verification/paged-fia-prefill-20261029.json"
        evidence["staged_prefill"] = {
            "recipe_case_path": str(recipe_case), "recipe_case_sha256": _hash(recipe_case),
            "paired_evidence_path": str(evidence_path),
            "paired_evidence_sha256": _hash(evidence_path),
            "selection": deepcopy(recipe),
            "copied_scope": "flash_attention_prefill_recipe_only",
            "storage": storage, "kv_storage_policy": policy,
            "basis": "caller_selected_recipe_and_storage; no_measured_duration_input",
            "capture_dispatch_identity_verified": False,
            "physical_work_scope": "semantic_contract; prediction_executes_selected_recipe",
        }
        if key == "a5_qwen38":
            steady_path = (sim / "data/verification/matrix-cohort-wave4-20261029"
                           / "a5_qwen38-steady.case.json")
            steady = _read(steady_path)["runtime"]["kernels"]["programs"]["matmul"]
            kernels.setdefault("programs", {})["matmul"] = deepcopy(steady)
            overrides["kernels.programs.matmul"] = deepcopy(steady)
            evidence["steady_matrix"] = {
                "case_path": str(steady_path), "case_sha256": _hash(steady_path),
                "selection": deepcopy(steady), "copied_scope": "matmul_program_only",
                "capture_dispatch_identity_verified": False,
                "attention_internal_matrix_uses_staged_recipe": True,
            }
        suffix = f"{key}_{storage}_prefill_" + (
            "combined" if key == "a5_qwen38" else "staged")
        value.update(
            name=suffix + "-selected", declaration_key=suffix,
            variant="source_combined_prefill_conditional",
        )
        source["override_basis"] = "composed_independent_source_recipes"
        result.append(value)
    return result


def variants(key, old, base):
    values = [_variant(key, old, base)]
    if "glm53" in key or key in {"a3_v4f", "a3_v4pro"}:
        values.append(_variant(key, old, base, fused=True))
        if key in {"a3_v4f", "a3_v4pro"}:
            values.append(_compressor_fp32_variant(key, old, base))
    elif key == "a5_kimi_k3":
        values.append(_variant(key, old, base, decode=True))
        values.extend(_variant(key, old, base, decode=decode, checkpoint=True)
                      for decode in (False, True))
        values.extend(_kimi_single_group_variant(key, old, base, decode=decode)
                      for decode in (False, True))
        values.append(_kimi_sp_variant(key, old, base))
    elif key == "a5_qwen38":
        values.append(_steady_matmul_variant(key, old, base))
    if key in {"a3_glm53_prefill", "a3_glm53_decode", "a3_v4f"}:
        values.append(_shared_quant_variant(key, old, base))
    from fusion_replay_paged_cases import paged_variants

    values.extend(paged_variants(key, values[0]))
    values.extend(_staged_paged_variants(key, values))
    values.extend(_combined_prefill_variants(key, values))
    from replay_scfa_readiness import scfa_variant

    scfa = scfa_variant(key, values[0])
    if scfa is not None:
        values.append(scfa)
    return values
