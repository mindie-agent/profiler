"""Per-operator ABI observation bundles and ideal hardware Roofline bounds (modeling_inputs_roofline).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting per-operator abi observation bundles and ideal hardware roofline bounds.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .modeling_inputs_observations import OperatorObservation
from .modeling_inputs_slots import SCHEMA_VERSION

@dataclass(frozen=True, init=False)
class ModelingInputsBundle:
    """Portable collection of operator observations consumed by a simulator."""

    schema_version: str; observations: tuple[OperatorObservation, ...]
    generated_at: str | None; source: str | None; metadata: dict[str, Any]

    def __init__(self, observations: Iterable[OperatorObservation | Mapping[str, Any]] = (),
                 *, schema_version: str = SCHEMA_VERSION, generated_at: str | None = None,
                 source: str | None = None, metadata: Mapping[str, Any] | None = None) -> None:
        normalized: list[OperatorObservation] = []
        for item in observations:
            if isinstance(item, OperatorObservation):
                normalized.append(item)
            elif isinstance(item, Mapping):
                normalized.append(OperatorObservation.from_mapping(item))
            else:
                raise TypeError("observations must contain OperatorObservation or mappings")
        object.__setattr__(self, "schema_version", str(schema_version))
        object.__setattr__(self, "observations", tuple(normalized))
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ModelingInputsBundle":
        if not isinstance(value, Mapping):
            raise TypeError("modeling inputs bundle must be a mapping")
        return cls(
            observations=value.get("observations", ()),
            schema_version=value.get("schema_version", SCHEMA_VERSION),
            generated_at=value.get("generated_at"),
            source=value.get("source"),
            metadata=value.get("metadata"),
        )

    from_dict = from_mapping

    def as_dict(self) -> dict[str, Any]:
        family_counts: dict[str, int] = {}
        for observation in self.observations:
            family_counts[observation.family] = family_counts.get(observation.family, 0) + 1
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source": self.source,
            "observation_count": len(self.observations),
            "families": dict(sorted(family_counts.items())),
            "observations": [observation.as_dict() for observation in self.observations],
            "metadata": dict(self.metadata),
        }

    to_dict = as_dict

    def __len__(self) -> int:
        return len(self.observations)

    def __iter__(self):
        return iter(self.observations)

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]
