"""Score service-response replay without granting cancellation credit.

[Role] Turn ordered per-capture parts or native-call observations into the
  signed, uncancelled and cancellation-mass error statistics used by release
  acceptance.
[Invariants] Every part contributes its declared ``count`` multiplicity. A
  missing or non-finite prediction is an incomplete acceptance, never a zero
  error. Opposite-sign residuals may make the signed aggregate vanish; they
  can never make ``uncancelled_L1`` vanish.
[Timeouts & Locks] Pure finite arithmetic over caller-owned sequences; no I/O,
  waits, locks, subprocesses or device work.
[Side-Effect Policy] Read-only over the supplied parts; returns new values.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import math


SCHEMA = "mindie-profiler-service-response-acceptance/1"
DEFAULT_TOLERANCE = 0.10


class AcceptanceError(ValueError):
    """An acceptance input is malformed or an expectation was not met."""


def _number(value, *, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AcceptanceError(f"acceptance_{field}_requires_number")
    number = float(value)
    if not math.isfinite(number):
        raise AcceptanceError(f"acceptance_{field}_requires_finite_number")
    return number


def part_weight(part):
    """Return the strict observation multiplicity of one ordered part.

    The service-response corpus records multiplicities as ``count``. A
    ``weight`` field is not an accepted substitute because substituting a
    default silently changes the population being scored.
    """
    if not isinstance(part, Mapping):
        raise AcceptanceError("acceptance_part_requires_mapping")
    if "count" not in part:
        raise AcceptanceError("acceptance_part_requires_count")
    count = part["count"]
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise AcceptanceError("acceptance_part_count_requires_positive_integer")
    return count


def _observed_predicted(part):
    """Read one part's observed/predicted durations without inventing values."""
    status = part.get("status")
    if status not in (None, "compared", "completed", "ok"):
        raise AcceptanceError(f"acceptance_part_unresolved:{status}")
    observed = predicted = None
    for observed_key, predicted_key in (
        ("observed_ms", "predicted_ms"),
        ("observed", "predicted"),
    ):
        if observed_key in part:
            observed = _number(part[observed_key], field="observed")
        if predicted_key in part:
            predicted = _number(part[predicted_key], field="predicted")
        if observed is not None or predicted is not None:
            break
    if observed is None:
        raise AcceptanceError("acceptance_part_requires_observed_duration")
    if observed <= 0.0:
        raise AcceptanceError("acceptance_part_observed_requires_positive_duration")
    if predicted is None:
        # The replay corpus records an observed duration plus its residual.
        # Requiring an explicit predicted value would let a missing prediction
        # masquerade as an absent field; derive it only from a declared error.
        if "relative_error" in part:
            error = _number(part["relative_error"], field="relative_error")
            predicted = observed * (1.0 + error)
        elif "prediction_ms" in part:
            predicted = _number(part["prediction_ms"], field="predicted")
        else:
            raise AcceptanceError("acceptance_part_requires_prediction")
    if not math.isfinite(predicted) or predicted < 0.0:
        raise AcceptanceError("acceptance_part_predicted_requires_nonnegative_duration")
    return observed, predicted


def _weights_and_residuals(parts):
    if isinstance(parts, (str, bytes)) or not isinstance(parts, Sequence):
        raise AcceptanceError("acceptance_requires_ordered_parts")
    if not parts:
        raise AcceptanceError("acceptance_requires_nonempty_parts")
    rows = []
    for index, part in enumerate(parts):
        weight = part_weight(part)
        observed, predicted = _observed_predicted(part)
        rows.append({
            "index": index,
            "display_id": part.get("id", part.get("task")),
            "count": weight,
            "observed_ms": observed,
            "predicted_ms": predicted,
            "residual_ms": predicted - observed,
        })
    return rows


def acceptance_metrics(parts):
    """Compute O/P/N and the three uncancelled statistics for ordered parts.

    ``e_i = predicted_i - observed_i`` and every sum is weighted by the part's
    declared ``count``::

        O = sum w_i * observed_i
        P = sum w_i * max(e_i, 0)
        N = sum w_i * max(-e_i, 0)

        signed_relative_error = (P - N) / O
        uncancelled_L1        = (P + N) / O
        cancellation_mass     = 2 * min(P, N)

    Duplicate display identifiers are retained as distinct ordered rows; the
    row index, never the identifier, identifies a part.
    """
    rows = _weights_and_residuals(parts)
    observed_mass = 0.0
    positive_mass = 0.0
    negative_mass = 0.0
    for row in rows:
        weight = row["count"]
        observed_mass += weight * row["observed_ms"]
        residual = row["residual_ms"]
        positive_mass += weight * max(residual, 0.0)
        negative_mass += weight * max(-residual, 0.0)
    if observed_mass <= 0.0 or not math.isfinite(observed_mass) or not math.isfinite(positive_mass) or not math.isfinite(negative_mass):
        raise AcceptanceError("acceptance_requires_positive_finite_observed_mass")
    signed = (positive_mass - negative_mass) / observed_mass
    uncancelled = (positive_mass + negative_mass) / observed_mass
    if not (math.isfinite(signed) and math.isfinite(uncancelled)):
        raise AcceptanceError("acceptance_mass_overflow")
    for row in rows:
        row["weighted_abs_residual_ms"] = row["count"] * abs(row["residual_ms"])
    worst = max(rows, key=lambda row: (
        row["weighted_abs_residual_ms"], row["index"]))
    return {
        "schema_version": SCHEMA,
        "part_count": len(rows),
        "total_count": sum(row["count"] for row in rows),
        "observed_mass_ms": observed_mass,
        "positive_mass_ms": positive_mass,
        "negative_mass_ms": negative_mass,
        "signed_relative_error": signed,
        "uncancelled_L1": uncancelled,
        "cancellation_mass": 2.0 * min(positive_mass, negative_mass),
        "aggregate_relative_error": (positive_mass - negative_mass) / observed_mass,
        "parts": rows,
        "worst_part": {
            "index": worst["index"],
            "display_id": worst["display_id"],
            "count": worst["count"],
            "observed_ms": worst["observed_ms"],
            "predicted_ms": worst["predicted_ms"],
            "relative_error": (worst["residual_ms"] / worst["observed_ms"]
                               if worst["observed_ms"] else None),
        },
    }


def signed_relative_error(parts):
    """Signed aggregate residual ``(P - N) / O`` for ordered parts."""
    return acceptance_metrics(parts)["signed_relative_error"]


def uncancelled_l1(parts):
    """Uncancelled residual ``(P + N) / O``; opposite signs cannot cancel."""
    return acceptance_metrics(parts)["uncancelled_L1"]


def cancellation_mass(parts):
    """Absolute opposite-sign mass ``2 * min(P, N)`` in observed-duration ms."""
    return acceptance_metrics(parts)["cancellation_mass"]


def evaluate_acceptance(parts, *, tolerance=DEFAULT_TOLERANCE, label=None):
    """Return one capture's acceptance decision from uncancelled L1.

    Missing predictions, missing counts and malformed values produce an
    explicit incomplete result rather than a passing or zero-error part.
    """
    tolerance = _number(tolerance, field="tolerance")
    if tolerance < 0.0:
        raise AcceptanceError("acceptance_tolerance_requires_nonnegative")
    try:
        metrics = acceptance_metrics(parts)
    except AcceptanceError as exc:
        return {
            "schema_version": SCHEMA,
            "status": "incomplete",
            "passed": False,
            "reason": str(exc),
            "label": label,
            "tolerance": tolerance,
        }
    metrics.update(status="evaluated",
                   passed=metrics["uncancelled_L1"] <= tolerance,
                   tolerance=tolerance, label=label)
    if metrics["passed"]:
        metrics["reason"] = "uncancelled_l1_within_tolerance"
    elif metrics["signed_relative_error"] == 0.0:
        metrics["reason"] = "cancellation_dependent_aggregate"
    else:
        metrics["reason"] = "uncancelled_l1_exceeds_tolerance"
    return metrics


def require_acceptance(parts, *, tolerance=DEFAULT_TOLERANCE, label=None):
    """Return metrics or raise when the uncancelled acceptance gate fails."""
    result = evaluate_acceptance(parts, tolerance=tolerance, label=label)
    if not result["passed"]:
        raise AcceptanceError(
            f"service_response_acceptance_failed:{result['reason']}:"
            f"uncancelled_L1={result.get('uncancelled_L1')!r}:"
            f"tolerance={tolerance!r}")
    return result


def native_call_acceptance(observations, predictions, *, counts=None,
                           tolerance=DEFAULT_TOLERANCE, label=None):
    """Score native-call observations against their calibrated predictions.

    ``observations`` and ``predictions`` are aligned sequences; ``counts`` is
    an optional aligned multiplicity sequence (default one occurrence each).
    A prediction that compensates for a previous operator's error is still a
    failing native call, because body totals are deliberately not scored here.
    """
    if isinstance(observations, (str, bytes)) or isinstance(predictions, (str, bytes)):
        raise AcceptanceError("native_acceptance_requires_sequences")
    observations = list(observations)
    predictions = list(predictions)
    if len(observations) != len(predictions):
        raise AcceptanceError("native_acceptance_length_mismatch")
    if counts is None:
        counts = [1] * len(observations)
    else:
        counts = list(counts)
        if len(counts) != len(observations):
            raise AcceptanceError("native_acceptance_count_length_mismatch")
    parts = []
    for index, (observed, predicted, count) in enumerate(
            zip(observations, predictions, counts)):
        parts.append({
            "index": index,
            "observed_ms": observed,
            "predicted_ms": predicted,
            "count": count,
        })
    return evaluate_acceptance(parts, tolerance=tolerance, label=label)


def corpus_acceptance(results):
    """Aggregate per-capture acceptance results without hiding a failing part.

    ``results`` are outputs of :func:`evaluate_acceptance`. The corpus passes
    only when every supplied capture was evaluated and passed; a single
    incomplete capture fails the corpus.
    """
    results = list(results)
    if not results:
        raise AcceptanceError("corpus_acceptance_requires_results")
    incomplete = [result for result in results
                  if result.get("status") != "evaluated"]
    failed = [result for result in results
              if result.get("status") == "evaluated" and not result.get("passed")]
    observed_mass = sum(result.get("observed_mass_ms", 0.0) for result in results)
    positive = sum(result.get("positive_mass_ms", 0.0) for result in results)
    negative = sum(result.get("negative_mass_ms", 0.0) for result in results)
    mass_ok = (math.isfinite(observed_mass) and math.isfinite(positive)
               and math.isfinite(negative) and math.isfinite(positive + negative))
    uncancelled = ((positive + negative) / observed_mass
                   if mass_ok and observed_mass > 0.0 else None)
    if uncancelled is not None and not math.isfinite(uncancelled):
        mass_ok = False
        uncancelled = None
    return {
        "schema_version": SCHEMA,
        "status": "evaluated" if (mass_ok and not incomplete) else "incomplete",
        "reason": ("corpus_acceptance_mass_overflow" if not mass_ok
                   else ("incomplete_captures" if incomplete
                         else ("failed_captures" if failed else "all_passed"))),
        "capture_count": len(results),
        "passed_count": sum(1 for result in results if result.get("passed")) if mass_ok else 0,
        "failed_count": len(failed),
        "incomplete_count": len(incomplete) if mass_ok else len(results),
        "failed_labels": [result.get("label") for result in failed],
        "incomplete_labels": [result.get("label") for result in incomplete],
        "observed_mass_ms": observed_mass if mass_ok else None,
        "uncancelled_L1": uncancelled,
        "passed": bool(mass_ok and not failed and not incomplete),
    }
