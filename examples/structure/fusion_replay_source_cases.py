"""Additional explicit source programs for retained GLM and Kimi replays.

[Role] Compose caller-selected programs onto existing independent declarations.
[Invariants] Models, geometry, device overrides and unrelated programs survive.
  A source choice establishes neither captured dispatch nor layer occurrence.
[Timeouts & Locks] Bounded source metadata reads; no subprocesses or locks.
[Side-Effect Policy] Import is inert. Calls read source identities and return
  new in-memory variants; no raw captures, predictions or files are changed.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path


INDEXED_IMPLEMENTATION = "ascend_sparse_flash_attention_arch22"
SITU_PROGRAM = "situ_mx_quant_arch35"


def _source_files(baseline, names):
    case_path = Path(baseline["declaration_source"]["case_path"]).resolve()
    root = next(parent for parent in case_path.parents
                if (parent / "mindie_sim").is_dir())
    files = []
    for name in names:
        path = root / name
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append({
            "path": str(path), "sha256": digest.hexdigest(),
            "size_bytes": path.stat().st_size,
        })
    return files


def _append_identity(value, baseline, suffix, variant):
    declaration = baseline["declaration_key"] + suffix
    value.update(
        name=declaration + "-selected", declaration_key=declaration,
        variant=variant,
    )
    source = value["declaration_source"]
    source.update(
        base_variant=baseline["variant"],
        base_declaration_key=baseline["declaration_key"],
        override_basis="composed_explicit_source_programs",
        capture_dispatch_identity_verified=False,
        replaces_reference_variant=False,
    )
    source["implementation_overrides"] = deepcopy(
        value["case"]["runtime"]["kernels"]["lowerings"])
    return source


def _indexed_variant(baseline):
    value = deepcopy(baseline)
    selection = {
        "implementation": INDEXED_IMPLEMENTATION,
        "options": {"scratch_policy": "offchip"},
    }
    case = value["case"]
    case["runtime"]["kernels"]["lowerings"]["indexed_attention"] = selection
    case["machine"]["backend"] = "ascend"
    source = _append_identity(
        value, baseline, "_indexed_arch22",
        "source_shared_quant_indexed_arch22_conditional",
    )
    source["machine_overrides"] = {
        **source.get("machine_overrides", {}), "backend": "ascend",
    }
    source.setdefault("source_evidence", {})["indexed_attention_program"] = {
        "selection": deepcopy(selection),
        "source_revision": "8fd0bc4885cb52e58791aaa8efacc571b9bd115d",
        "source_scope": "arch22_sparse_flash_attention_MLA_V_TEMPLATE",
        "files": _source_files(baseline, (
            "mindie_sim/prediction/indexed_attention.py",
            "mindie_sim/backends/profiles/ascend.json",
            "data/verification/sparse-attention-mechanism-20261029.json",
        )),
        "copied_scope": "indexed_attention_lowering_and_explicit_backend",
        "hardware_basis": "registered_nominal_profile_with_existing_device_overrides",
        "device_overrides_changed": False,
        "geometry_changed": False, "model_precision_changed": False,
        "capture_dispatch_identity_verified": False,
        "index_values_observed": False,
        "limitations": [
            "Offchip scratch is an explicit caller condition, not inferred cache behavior.",
            "The source program requires BF16 dense latent MLA, one contiguous sequence, "
            "block-size-one indices and paired AIC/AIV copy roles.",
            "Scalar lookup, cross-core flags, atomic response and cache eviction "
            "remain outside the declared mechanism.",
            "Finite owner placement and operand service modes use the declared profile; "
            "they are not measured historical instruction rates.",
        ],
    }
    return value


def _situ_variant(baseline):
    value = deepcopy(baseline)
    fusion = value["case"]["runtime"]["kernels"]["lowerings"]["native_fusion"]
    options = fusion["options"]
    # The complete program owns the entire call. Keeping the older traffic-only
    # savings on this role would subtract the same intermediate a second time.
    traffic = options.get("traffic_profile", "preserve_workspaces")
    previous = (traffic.get("situ_quant", "preserve_workspaces")
                if isinstance(traffic, dict) else traffic)
    if isinstance(traffic, dict):
        traffic["situ_quant"] = "preserve_workspaces"
    else:
        options["traffic_profile"] = {
            role: "preserve_workspaces" if role == "situ_quant" else traffic
            for role in options["roles"]
        }
    options.setdefault("program_profiles", {})["situ_quant"] = SITU_PROGRAM
    source = _append_identity(
        value, baseline, "_situ_arch35",
        "source_checkpoint_situ_arch35_conditional",
    )
    source.setdefault("source_evidence", {})["situ_quant_program"] = {
        "program": SITU_PROGRAM,
        "source_base_revision": "175ef4d49c2072f9233619636f0309f4f88b4e2c",
        "source_state": "added_in_index",
        "files": _source_files(baseline, (
            "mindie_sim/prediction/family_situ_mx.py",
            "docs/operators/situ-mx-quant.md",
        )),
        "copied_scope": "situ_quant_complete_program_only",
        "replaced_role_traffic_profile": previous,
        "member_traffic_savings_applied_again": False,
        "device_overrides_changed": False,
        "geometry_changed": False, "model_precision_changed": False,
        "scalar_parameters_basis": "existing_independent_model_declaration",
        "capture_dispatch_identity_verified": False,
        "limitations": [
            "Current checkpoint metadata remains conditional for the historical capture.",
            "The selected source hashes do not identify the captured binary or tiling key.",
            "Beta, linear_beta, activation-half selection and axis are model declarations; "
            "capture descriptors do not observe their values.",
            "The source program requires exactly SiTU plus its quantization consumer; "
            "an externally consumed BF16 intermediate remains unsupported.",
        ],
    }
    return value


def source_program_variants(key, baseline):
    """Append source arms to the named baselines; never replace old declarations."""
    if (key == "a3_glm53_decode"
            and baseline["variant"] == "source_shared_int32_conditional"):
        return [_indexed_variant(baseline)]
    if (key == "a5_kimi_k3"
            and baseline["variant"] == "current_checkpoint_conditional"):
        return [_situ_variant(baseline)]
    return []
