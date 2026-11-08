"""Use declared native observation profiles in offline capture replay.

[Role] Bind maintained physical input profiles before the ordinary Body API.
[Invariants] Simulator and observation identities remain separate. Domain misses
  preserve the caller's prediction; observed spans never enter this adapter.
[Timeouts & Locks] Small local files are fingerprinted once per evaluator process;
  each call builds only its finite input geometry. No locks or subprocesses.
[Side-Effect Policy] Read profile files and return new inputs/results only.
"""
from hashlib import sha256
from pathlib import Path

from body import predict_body as _predict_body


ROOT = Path(__file__).resolve().parent
PROFILE_FILES = (
    "native_observations.py", "a2_native_observations.py", "a5_native_observations.py",
    "a3_mla_native_observations.py", "profiles/a3_sharedkv_output_a_20261107.json",
    "a5_mtp_native_observations.py",
    "a5_q35_unfused_native_observations.py",
    "capture_policy.py", "capture_structure.py", "capture_ffn_guard.py", "capture_mla_structure.py",
    # Phase/geometry-scoped caller projection and its source/tensor validators.
    "capture_scoped_structure.py", "capture_scoped_contracts.py",
    "capture_scoped_evidence.py", "capture_scoped_geometry.py",
    # A3 prefill FlashAttention/AllReduce native responses and their builder.
    "prefill_native_observations.py", "prefill_native_builder.py",
    # Archive calibration qualification changes the input before native replay.
    "wave5_regime_import.py",
    # Shared C-before-B per-capture replay integration and uncancelled gates.
    "scoped_native_replay.py", "dsh_scoped_prefill.py",
    "service_response_acceptance.py",
    "dsh_generalization_eval.py", "wave5_generalization_eval.py",
    "profiles/a3_static_service_20261107.json",
    # Explicit-qualified A2/A5 calibration arm; data and selector semantics.
    "qualified_native_calibration.py", "qualified_native_abi.py",
    "profiles/a2_fia_dense_qualified_20261107.json",
    "profiles/a5_attention_qualified_20261107.json",
    "profiles/a2_native_20261031.json", "profiles/a2_decode_native_20261031.json",
    "profiles/a5_gdn_decode_native_20261106.json", "profiles/a5_mtp_native_20261106.json",
    "profiles/a5_q35_unfused_native_20261106.json",
    "profiles/a5_q35_q1_unfused_native_20261106.json",
    "profiles/prefill_native_20261106.json",
)


PROFILER_SOURCE_FILES = (
    "normalized.py", "sources_csv.py", "sources_db.py", "events.py",
    "native_tensor_abi.py", "body_moe_contracts.py", "body_matrix_contracts.py",
    "knowledge/db_source_mapping.json",
)


def native_observation_identity(root=ROOT, source_root=None):
    """Include adapter semantics, reused decoders and response data."""
    digest = sha256(b"mindie-profiler-native-observations/1\0")
    for relative in PROFILE_FILES:
        digest.update(relative.encode("utf-8") + b"\0")
        with (Path(root) / relative).open("rb") as handle:
            content = sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content.update(chunk)
        digest.update(content.digest())
    if source_root is None:
        import mindie_profiler
        source_root = Path(mindie_profiler.__file__).resolve().parent
    for relative in PROFILER_SOURCE_FILES:
        digest.update(b"profiler-source\0" + relative.encode("utf-8") + b"\0")
        with (Path(source_root) / relative).open("rb") as handle:
            content = sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content.update(chunk)
        digest.update(content.digest())
    return digest.hexdigest()


def apply_native_observations(raw, *, phase, tokens, context, sequences=1,
                              qualified=()):
    """Select physical profiles explicitly for the observed-native replay arm.

    The A3 prefill FlashAttention/AllReduce response is the last native profile,
    after the existing A2/A5/MTP/unfused adapters. ``qualified`` is an explicit
    sequence of ``(profile_name, actual_native_abi)`` pairs; it defaults to no
    qualified arm, so archived default replay is unchanged. Callers still gate
    ordinary modeling; an out-of-domain adapter is a copied no-op with a reason.
    """
    from a2_native_observations import apply_a2_native_observations
    from a3_mla_native_observations import apply_a3_mla_native_observations
    from a5_native_observations import apply_a5_native_observations
    from a5_mtp_native_observations import apply_a5_mtp_native_observations
    from a5_q35_unfused_native_observations import apply_a5_q35_unfused_native_observations
    from prefill_native_observations import apply_prefill_native_observations
    from qualified_native_calibration import apply_qualified_native_observations

    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    result, a2 = apply_a2_native_observations(raw, **geometry)
    result, a5 = apply_a5_native_observations(result, **geometry)
    result, mtp = apply_a5_mtp_native_observations(result, **geometry)
    result, unfused = apply_a5_q35_unfused_native_observations(result, **geometry)
    result, prefill = apply_prefill_native_observations(result, **geometry)
    result, a3_mla = apply_a3_mla_native_observations(result, **geometry)
    qualified_results = []
    for name, abi in qualified:
        result, selected = apply_qualified_native_observations(
            result, profile=name, native_abi=abi, **geometry)
        qualified_results.append(selected)
    return result, {"arm": "observed_native",
                    "profiles": [a2, a5, mtp, unfused, prefill, a3_mla],
                    "prefill_native": prefill,
                    "qualified_profiles": qualified_results,
                    "observations_modified": False, "body_total_fitting": False}


def predict_declared_body(raw, *, phase="decode", tokens, context, sequences=1):
    """Price an already-adapted raw without re-applying native profiles."""
    return _predict_body(raw, phase=phase, tokens=tokens, context=context,
                         sequences=sequences)


def predict_body(raw, *, phase="decode", tokens, context, sequences=1, scope=None,
                 qualified=()):
    """Retain calibration provenance alongside the unchanged common Body API.

    ``scope`` is an optional per-capture prepared replay context
    (scoped_native_replay.PreparedScopedReplay). It applies the scoped caller
    before the native profiles and returns one combined provenance; the legacy
    call without a scope keeps the prior behavior exactly. ``qualified`` is an
    explicit opt-in sequence of named profiles plus their actual native ABI.
    """
    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    if scope is not None and qualified:
        raise ValueError("qualified_profiles_not_supported_with_prepared_scope")
    if scope is None:
        declared, provenance = apply_native_observations(raw, qualified=qualified, **geometry)
    else:
        declared, provenance = scope.apply(raw, **geometry)
    predicted = _predict_body(declared, **geometry)
    predicted["native_observation_provenance"] = provenance
    return predicted
