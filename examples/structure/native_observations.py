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
    "a5_mtp_native_observations.py",
    "a5_q35_unfused_native_observations.py",
    "capture_policy.py",
    "profiles/a2_native_20261031.json", "profiles/a2_decode_native_20261031.json",
    "profiles/a5_gdn_decode_native_20261106.json", "profiles/a5_mtp_native_20261106.json",
    "profiles/a5_q35_unfused_native_20261106.json",
    "profiles/a5_q35_q1_unfused_native_20261106.json",
)


def native_observation_identity(root=ROOT):
    """Include adapter semantics and response data, independently of Sim code."""
    digest = sha256(b"mindie-profiler-native-observations/1\0")
    for relative in PROFILE_FILES:
        digest.update(relative.encode("utf-8") + b"\0")
        with (Path(root) / relative).open("rb") as handle:
            content = sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content.update(chunk)
        digest.update(content.digest())
    return digest.hexdigest()


def apply_native_observations(raw, *, phase, tokens, context, sequences=1):
    """Select physical profiles explicitly for the observed-native replay arm."""
    from a2_native_observations import apply_a2_native_observations
    from a5_native_observations import apply_a5_native_observations
    from a5_mtp_native_observations import apply_a5_mtp_native_observations
    from a5_q35_unfused_native_observations import apply_a5_q35_unfused_native_observations

    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    result, a2 = apply_a2_native_observations(raw, **geometry)
    result, a5 = apply_a5_native_observations(result, **geometry)
    result, mtp = apply_a5_mtp_native_observations(result, **geometry)
    result, unfused = apply_a5_q35_unfused_native_observations(result, **geometry)
    return result, {"arm": "observed_native", "profiles": [a2, a5, mtp, unfused],
                    "observations_modified": False, "body_total_fitting": False}


def predict_body(raw, *, phase="decode", tokens, context, sequences=1):
    """Retain calibration provenance alongside the unchanged common Body API."""
    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    declared, provenance = apply_native_observations(raw, **geometry)
    predicted = _predict_body(declared, **geometry)
    predicted["native_observation_provenance"] = provenance
    return predicted
