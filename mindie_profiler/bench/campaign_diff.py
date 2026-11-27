"""Pure-CPU cross-version silicon benchmark campaign diffing (CANN / VA A/B).

[Role]
  Compare two version-fingerprinted campaign buckets (e.g. CANN ``9.3`` vs
  ``9.4`` or two ``va_commit`` revisions) inside a ``CampaignStore`` by joining
  on ``(canonical_key_digest, capture_mode, residency)``, surfacing per-kernel
  speedups/regressions, newly-supported and newly-broken ABIs, and optional
  plan-weighted per-model projections.

[Invariants]
  * Pure CPU (``DEV-ZERO-CTX``): never imports ``torch``, ``torch_npu``, or
    ``mindie_sim``.
  * Every emitted diff report passes ``abi_portable.portable_receipt()``.
  * Plan-weighted deltas are explicitly labeled as linear occurrence sums (DAG
    step-level replay belongs to ``mindie-sim``).

[Timeouts & Locks]
  Read-only bucket inspection plus atomic ``--out`` write via ``os.replace``.

[Side-Effect Policy]
  Writes only the optional caller-requested ``--out`` JSON path.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import sys
from typing import Any

from ..events import ProfilerUsageError
from .abi_portable import portable_receipt
from .campaign_store import CampaignStore
from .env_fingerprint import STATIC_BUCKET_KEYS
from .profiles import profile_section

DIFF_SCHEMA = "mindie-bench-diff/1"
_CAMPAIGN_CFG = profile_section("campaign")
_ROUND_US = int(profile_section("timing")["round_us_digits"])
_ROUND_PCT = int(_CAMPAIGN_CFG["round_pct_digits"])
_EXIT_ERR = int(_CAMPAIGN_CFG["exit_error"])


def _resolve_bucket_id(store: CampaignStore, selector: str) -> str:
    buckets = store.list_buckets()
    if selector in buckets:
        return selector
    matches = [bid for bid in buckets if selector in bid]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ProfilerUsageError(f"bench_diff_bucket_not_found: {selector!r}")
    raise ProfilerUsageError(
        f"bench_diff_bucket_ambiguous: {selector!r} matched {matches}"
    )


def _env_delta(base_env: Mapping[str, Any], cand_env: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for key in STATIC_BUCKET_KEYS:
        if base_env.get(key) != cand_env.get(key):
            changes[key] = {"base": base_env.get(key), "cand": cand_env.get(key)}
    return changes


def _metric_float(entry: Mapping[str, Any], key: str) -> float | None:
    value = entry.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    stats = entry.get("stats_us")
    if isinstance(stats, Mapping):
        short = key.removesuffix("_us")
        sub = stats.get(short)
        if isinstance(sub, (int, float)) and not isinstance(sub, bool):
            return float(sub)
    return None


def _is_ok_entry(entry: Mapping[str, Any]) -> bool:
    return (
        entry.get("status") == "ok"
        and entry.get("qualified") is True
        and _metric_float(entry, "p50_us") is not None
    )


def _plan_weighted_deltas(
    plan: Mapping[str, Any],
    deltas_by_case_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reverse_index = plan.get("reverse_index")
    if not isinstance(reverse_index, Mapping):
        return []
    aggregates: dict[tuple[Any, ...], dict[str, Any]] = {}
    for case_id, refs in reverse_index.items():
        kernel = deltas_by_case_id.get(str(case_id))
        if kernel is None or not isinstance(refs, Sequence):
            continue
        for ref in refs:
            if not isinstance(ref, Mapping):
                continue
            model_id = str(ref.get("model_id") or "")
            sku = str(ref.get("sku") or "")
            phase = str(ref.get("phase") or "")
            seq_len = ref.get("seq_len")
            concurrency = ref.get("concurrency")
            parallel_arm = str(ref.get("parallel_arm") or "")
            coord = (model_id, sku, phase, seq_len, concurrency, parallel_arm)
            occ = int(ref.get("occurrence_count") or 1)
            bucket = aggregates.setdefault(
                coord,
                {
                    "model_id": model_id,
                    "sku": sku,
                    "phase": phase,
                    "seq_len": seq_len,
                    "concurrency": concurrency,
                    "parallel_arm": parallel_arm,
                    "base_linear_sum_us": 0.0,
                    "cand_linear_sum_us": 0.0,
                    "matched_occurrences": 0,
                    "basis": "linear_occurrence_sum_not_dag_replay",
                },
            )
            bucket["base_linear_sum_us"] += float(kernel["base_p50_us"]) * occ
            bucket["cand_linear_sum_us"] += float(kernel["cand_p50_us"]) * occ
            bucket["matched_occurrences"] += occ
    out: list[dict[str, Any]] = []
    for item in aggregates.values():
        base_sum = item["base_linear_sum_us"]
        cand_sum = item["cand_linear_sum_us"]
        delta = cand_sum - base_sum
        item["base_linear_sum_us"] = round(base_sum, _ROUND_US)
        item["cand_linear_sum_us"] = round(cand_sum, _ROUND_US)
        item["delta_linear_sum_us"] = round(delta, _ROUND_US)
        item["delta_pct"] = round((delta / base_sum) * 100.0, _ROUND_PCT) if base_sum > 0 else None
        out.append(item)
    return sorted(out, key=lambda x: (x["model_id"], str(x["phase"]), int(x["seq_len"] or 0)))


def diff_buckets(
    campaign_dir: str | Path,
    *,
    base: str,
    cand: str,
    plan: Mapping[str, Any] | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    """Compare two environment buckets inside ``campaign_dir`` on pure CPU."""
    store = CampaignStore(campaign_dir)
    base_id = _resolve_bucket_id(store, base)
    cand_id = _resolve_bucket_id(store, cand)
    base_env = store.load_env(base_id)
    cand_env = store.load_env(cand_id)
    base_entries = dict(store.load_index(base_id).get("entries") or {})
    cand_entries = dict(store.load_index(cand_id).get("entries") or {})

    all_keys = sorted(set(base_entries) | set(cand_entries))
    kernels: list[dict[str, Any]] = []
    newly_supported: list[dict[str, Any]] = []
    newly_broken: list[dict[str, Any]] = []
    skipped_incompatible: list[dict[str, Any]] = []
    deltas_by_case_id: dict[str, dict[str, Any]] = {}

    for key in all_keys:
        b = base_entries.get(key)
        c = cand_entries.get(key)
        b_ok = isinstance(b, Mapping) and _is_ok_entry(b)
        c_ok = isinstance(c, Mapping) and _is_ok_entry(c)
        if b_ok and c_ok:
            b_clk = str(b.get("clock_operator") or "elapsed_span")
            c_clk = str(c.get("clock_operator") or "elapsed_span")
            if b_clk != c_clk:
                skipped_incompatible.append({
                    "entry_key": key,
                    "case_id": str(c.get("case_id") or b.get("case_id") or ""),
                    "reason": f"clock_operator_mismatch:{b_clk}!={c_clk}",
                })
                continue
            b_p50 = float(_metric_float(b, "p50_us") or 0.0)
            c_p50 = float(_metric_float(c, "p50_us") or 0.0)
            delta_us = c_p50 - b_p50
            delta_pct = ((delta_us / b_p50) * 100.0) if b_p50 > 0 else None
            speedup = (b_p50 / c_p50) if c_p50 > 0 else None
            row = {
                "entry_key": key,
                "case_id": str(c.get("case_id") or b.get("case_id") or ""),
                "canonical_key_digest": str(c.get("canonical_key_digest") or b.get("canonical_key_digest") or ""),
                "capture_mode": str(c.get("capture_mode") or b.get("capture_mode") or "eager"),
                "residency": str(c.get("residency") or b.get("residency") or "cold_hbm"),
                "bench_builder": c.get("bench_builder") or b.get("bench_builder"),
                "upstream_abi": c.get("upstream_abi") or b.get("upstream_abi"),
                "base_p50_us": round(b_p50, _ROUND_US),
                "cand_p50_us": round(c_p50, _ROUND_US),
                "base_min_us": _metric_float(b, "min_us"),
                "cand_min_us": _metric_float(c, "min_us"),
                "base_p99_us": _metric_float(b, "p99_us"),
                "cand_p99_us": _metric_float(c, "p99_us"),
                "base_iqr_us": _metric_float(b, "iqr_us"),
                "cand_iqr_us": _metric_float(c, "iqr_us"),
                "base_hbm_peak_bytes": b.get("hbm_peak_bytes"),
                "cand_hbm_peak_bytes": c.get("hbm_peak_bytes"),
                "delta_p50_us": round(delta_us, _ROUND_US),
                "delta_p50_pct": None if delta_pct is None else round(delta_pct, _ROUND_PCT),
                "speedup": None if speedup is None else round(speedup, _ROUND_PCT),
            }
            kernels.append(row)
            deltas_by_case_id[row["case_id"]] = row
        elif c_ok and isinstance(b, Mapping):
            newly_supported.append({
                "entry_key": key,
                "case_id": str(c.get("case_id") or ""),
                "base_status": str(b.get("status") or "absent"),
                "cand_p50_us": _metric_float(c, "p50_us"),
                "upstream_abi": c.get("upstream_abi"),
            })
        elif b_ok and isinstance(c, Mapping):
            newly_broken.append({
                "entry_key": key,
                "case_id": str(b.get("case_id") or ""),
                "base_p50_us": _metric_float(b, "p50_us"),
                "cand_status": str(c.get("status") or "absent"),
                "cand_error": c.get("abi_error") or c.get("reason"),
                "upstream_abi": b.get("upstream_abi"),
            })

    report: dict[str, Any] = {
        "schema": DIFF_SCHEMA,
        "status": "ok",
        "base_env_fingerprint_id": base_id,
        "cand_env_fingerprint_id": cand_id,
        "env_delta": _env_delta(base_env, cand_env),
        "compared_count": len(kernels),
        "newly_supported_count": len(newly_supported),
        "newly_broken_count": len(newly_broken),
        "skipped_incompatible_count": len(skipped_incompatible),
        "kernels": kernels,
        "newly_supported": newly_supported,
        "newly_broken": newly_broken,
        "skipped_incompatible": skipped_incompatible,
    }
    if plan is not None:
        report["plan_id"] = plan.get("plan_id")
        report["plan_weighted_deltas"] = _plan_weighted_deltas(plan, deltas_by_case_id)
    resolved_home = os.environ.get("HOME") if home is None else home
    return portable_receipt(report, home=resolved_home)


def _diff_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench diff",
        description="Compare two version-fingerprinted silicon benchmark campaign buckets (pure CPU).",
        allow_abbrev=False,
    )
    parser.add_argument("--campaign-dir", required=True, help="campaign store directory")
    parser.add_argument("--base", required=True, help="baseline env_fingerprint_id or unique filter")
    parser.add_argument("--cand", required=True, help="candidate env_fingerprint_id or unique filter")
    parser.add_argument("--plan", default=None, help="optional mindie-bench-plan/2 for reverse-index weighting")
    parser.add_argument("--out", "--output", dest="output", default=None, help="atomic JSON output path")
    return parser


def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}.tmp.{os.getpid()}")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")}, sort_keys=True))
        return
    sys.stdout.write(text)


def main(argv: Sequence[str] | None = None) -> int:
    args = _diff_parser().parse_args(list(argv or ()))
    plan_payload: dict[str, Any] | None = None
    if args.plan:
        try:
            plan_payload = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        except TimeoutError:
            raise
        except (OSError, ValueError) as exc:
            _emit({"schema": DIFF_SCHEMA, "status": "error", "reason": str(exc)}, args.output)
            return _EXIT_ERR
    try:
        report = diff_buckets(
            args.campaign_dir,
            base=args.base,
            cand=args.cand,
            plan=plan_payload,
        )
    except ProfilerUsageError as exc:
        _emit({"schema": DIFF_SCHEMA, "status": "error", "reason": str(exc)}, args.output)
        return _EXIT_ERR
    _emit(report, args.output)
    return 0


__all__ = ["DIFF_SCHEMA", "diff_buckets", "main"]
