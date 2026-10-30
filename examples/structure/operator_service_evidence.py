"""Retain executed observable-service evidence in compact operator reports.

[Role] Project Engine cost parameters without copying calibration histograms.
[Invariants] Execution evidence never changes tensor admission or predictions.
  Serviced work is an Engine counter only when supplied by the cost result;
  response parameters and analytical reference work are labeled separately.
[Timeouts & Locks] Bounded parameter metadata, no subprocesses or locks.
[Side-Effect Policy] Pure projection; no measurements, simulation or writes.
"""
from hashlib import sha256
import json


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def service_execution_evidence(parameters, *, serviced=None):
    """Keep actual rule queries and their case-reconstructable declaration hash."""
    records = []
    for record in parameters.get("service_regimes", ()):
        declaration = {key: value for key, value in record.items()
                       if key not in {"model_id", "queries", "response_us_min", "response_us_max"}}
        provenance = record.get("provenance", {})
        records.append({
            "id": record["id"], "declaration_sha256": _digest(declaration),
            "provenance_sha256": _digest(provenance),
            "match": record.get("match", {}), "execution": record.get("execution"),
            "response": record.get("response"), "queries": dict(record.get("queries", {})),
            "response_us_min": record.get("response_us_min"),
            "response_us_max": record.get("response_us_max"),
            "calibration_origin": provenance.get("calibration_origin", "not_declared"),
            "evaluation_relation": provenance.get("evaluation_relation", "not_declared"),
            "body_residual_used": provenance.get("body_residual_used"),
        })
    return {
        "schema_version": "mindie-operator-service-execution/1",
        "basis": "executed_Sim_Engine_cost_parameters",
        "strict_admission_changed": False,
        "operator_occurrences": parameters.get("operator_occurrences"),
        "work_basis": parameters.get("work_basis"),
        "regime_selection": parameters.get("regime_selection"),
        "rules": records,
        "joint_native_services": parameters.get("joint_native_services", []),
        "serviced_resources": None if serviced is None else dict(serviced),
        "serviced_resources_basis": "not_retained" if serviced is None else "Engine_serviced_work_counter",
        "analytical_reference_work_executes_alongside_joint_service": False,
    }
