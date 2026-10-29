"""Prepare a new runtime arm over retained Decode observations.

[Role] Reuse source-pinned extractions and refresh only declared Sim inputs.
[Invariants] Later manifests replace the same case (for corrected local paths).
  Extraction bytes and measured geometry remain unchanged. Different source
  cases require explicit overrides; this tool never selects a model by timing.
[Timeouts & Locks] Bounded metadata reads and 10-second local Git queries.
[Side-Effect Policy] Read local cases/evidence; write one requested manifest.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError(f"metadata exceeds 50 MiB: {path}")
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest(),
            "size_bytes": path.stat().st_size}


def prepare(inputs, checkout, revision, variant, overrides=None, selected=None):
    checkout = Path(checkout).resolve()
    head = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    expected = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", revision], text=True, timeout=10).strip()
    if head != expected:
        raise ValueError("selected checkout is not at requested runtime commit")
    declarations, origins = {}, {}
    for path in inputs:
        path = Path(path).resolve()
        for row in read(path)["cases"]:
            declarations[row["case_id"]] = copy.deepcopy(row)
            origins[row["case_id"]] = path
    overrides = overrides or {}
    unknown = (set(overrides) | set(selected or ())) - declarations.keys()
    if unknown:
        raise ValueError(f"case IDs absent from input manifests: {sorted(unknown)}")
    cases = []
    for case_id, row in declarations.items():
        if selected and case_id not in selected:
            continue
        previous_case = row["replay_input_pins"]["case"]
        relative = overrides.get(case_id)
        if relative is None:
            relative = "examples/" + row["sim_case_path"].split("/examples/", 1)[1]
        case_path = checkout / relative
        if not case_path.resolve().is_relative_to(checkout):
            raise ValueError("Sim case override must stay inside selected checkout")
        extraction = Path(row["extraction_path"])
        if not extraction.is_absolute():
            extraction = origins[case_id].parent / extraction
        extraction_identity = identity(extraction)
        if extraction_identity["sha256"] != row["replay_input_pins"]["extraction"]["sha256"]:
            raise ValueError(f"retained extraction bytes changed: {case_id}")
        case_identity = identity(case_path)
        row.update(sim_case_path=str(case_path), extraction_path=str(extraction.resolve()),
                   variant_id=variant, model_declaration=case_identity)
        row["replay_input_pins"].update(case=case_identity, extraction={
            **extraction_identity, "reused_existing_extraction": True})
        row["runtime_refresh"] = {
            "prior_input_manifest": identity(origins[case_id]),
            "prior_case_identity": previous_case,
            "case_bytes_changed": previous_case["sha256"] != case_identity["sha256"],
            "explicit_case_override": case_id in overrides,
            "retained_extraction_bytes_unchanged": True,
        }
        cases.append(row)
    return {"schema_version": "mindie-decode-forward-replay/1", "variant_id": variant,
            "not_new_live_collection": True,
            "basis": "fresh runtime prediction using unchanged retained source populations",
            "runtime_plan": {"checkout": str(checkout), "source_commit": head},
            "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.input, args.checkout, args.revision, args.variant,
                     read(args.overrides) if args.overrides else {}, args.case_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases": len(result["cases"]), "output": identity(args.output)}))


if __name__ == "__main__":
    main()
