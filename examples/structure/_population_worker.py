"""Isolated worker entry for evaluating independent decode receipt populations.

[Role]
  Evaluate `mindie_sim.prediction.body.body_forward` for declared secondary
  receipt populations in a clean child process without importing fleet caches.

[Invariants]
  * Preserves exact declared case and `(tokens, context, sequences)` geometry.
  * Never reads measured timings or mutates shared state.

[Timeouts & Locks]
  Bounded by parent `proc.communicate(timeout=90)`; no locks or daemons.

[Side-Effect Policy]
  Reads request pickle and writes result pickle inside parent temporary dir.
"""
from __future__ import annotations

import pickle
from pathlib import Path
import sys

from mindie_sim.prediction.frontend.body_spec import body_forward


def run_slice(case, pending, idx: int, total: int) -> list:
    results = []
    for sub_key, sub_steps in pending[idx::total]:
        span = 0.0
        engine_query = None
        for tokens, context, sequences in sub_steps:
            raw = body_forward(
                case, phase="decode", tokens=tokens, context=context,
                sequences=sequences, event_limit=0, compact=True,
            )
            span += float(raw["body_forward_ms"])
            geom = raw.get("geometry") if isinstance(raw.get("geometry"), dict) else {}
            engine_query = {
                "valid_query_tokens": geom.get("valid_query_tokens"),
                "graph_query_tokens": geom.get("graph_query_tokens"),
                "padded_query_tokens": geom.get("padded_query_tokens"),
                "sequences_by_replica": geom.get("sequences_by_replica"),
                "valid_query_tokens_by_replica": geom.get("valid_query_tokens_by_replica"),
                "graph_query_tokens_by_replica": geom.get("graph_query_tokens_by_replica"),
                "padded_query_tokens_by_replica": geom.get("padded_query_tokens_by_replica"),
                "physical_global_ranks_by_replica": geom.get("physical_global_ranks_by_replica"),
                "physical_global_rank_basis": geom.get("physical_global_rank_basis"),
            }
        results.append((sub_key, {"predicted_step_ms": round(span, 9), "engine_query": engine_query}))
    return results


def main(argv: list[str]) -> int:
    req_path, out_path = Path(argv[0]), Path(argv[1])
    idx, total = int(argv[2]), int(argv[3])
    case, pending = pickle.loads(req_path.read_bytes())
    out_path.write_bytes(pickle.dumps(run_slice(case, pending, idx, total)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
