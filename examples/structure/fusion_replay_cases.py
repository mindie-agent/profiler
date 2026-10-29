"""Independent case and source choices for retained profiling replay.

[Role] Select explicit declarations without reading observed kernel descriptors.
[Invariants] Source-selected variants retain provenance and never become defaults.
  Historical observations do not identify checkpoint precision or native dispatch.
[Timeouts & Locks] Bounded metadata only, no device calls, network or locks.
[Side-Effect Policy] Reads local case/evidence JSON; creates in-memory declarations.
"""
from hashlib import sha256
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
    execution = {name: old["declared_execution"][name]
                 for name in ("phase", "tokens", "context", "sequences")}
    if decode:
        execution.update(phase="decode", tokens=1, context=32768)
    case_path = Path(old["declaration_source"]["case_path"])
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
    from fusion_replay_paged_cases import paged_variants

    values.extend(paged_variants(key, values[0]))
    return values
