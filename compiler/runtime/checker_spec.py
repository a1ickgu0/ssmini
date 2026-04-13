"""
Checker specification IR for runtime constraint validation.

This module defines the CheckerSpec data structure for validating
execution results against constraints.
"""

from dataclasses import dataclass, field
from typing import Union
from enum import Enum


class ConstraintType(str, Enum):
    """Type of constraint to validate."""
    EQUALITY = "equality"
    RANGE = "range"
    PRESENCE = "presence"
    RANGE_EXCLUSIVE = "range_exclusive"


class ComparisonOperator(str, Enum):
    """Comparison operators for constraint validation."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_EQ = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQ = ">="


@dataclass(frozen=True)
class ConstraintSpec:
    """
    A single constraint specification for runtime validation.

    Attributes:
        metric: The metric name to check (e.g., "signal_strength")
        constraint_type: Type of constraint (equality, range, presence)
        operator: Comparison operator for equality/range constraints
        value: Expected value (scalar for equality, dict for range)
        anchor: When to check ("start" or "end")
        required: Whether the metric must be present
    """
    metric: str
    constraint_type: ConstraintType
    operator: ComparisonOperator = ComparisonOperator.EQUALS
    value: Union[str, int, float, dict] = 0
    anchor: str = "end"
    required: bool = True

    def to_dict(self) -> dict:
        result = {
            "metric": self.metric,
            "constraint_type": self.constraint_type.value,
            "operator": self.operator.value,
            "value": self.value,
            "anchor": self.anchor,
            "required": self.required
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ConstraintSpec":
        return cls(
            metric=data["metric"],
            constraint_type=ConstraintType(data["constraint_type"]),
            operator=ComparisonOperator(data.get("operator", "==")),
            value=data.get("value", 0),
            anchor=data.get("anchor", "end"),
            required=data.get("required", True)
        )


@dataclass(frozen=True)
class CheckerSpec:
    """
    Complete checker specification for a scenario.

    Attributes:
        scenario_name: Name of the scenario
        constraints: List of constraints to validate
        accept_on: When to accept (all, any, none)
        coverage: Coverage requirements
    """
    scenario_name: str
    constraints: tuple[ConstraintSpec, ...] = field(default_factory=tuple)
    accept_on: str = "all"  # "all", "any", "none"
    coverage: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "constraints": [c.to_dict() for c in self.constraints],
            "accept_on": self.accept_on,
            "coverage": self.coverage
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CheckerSpec":
        constraints = tuple(
            ConstraintSpec.from_dict(c) for c in data.get("constraints", [])
        )
        return cls(
            scenario_name=data["scenario_name"],
            constraints=constraints,
            accept_on=data.get("accept_on", "all"),
            coverage=data.get("coverage", {})
        )


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of validating a single constraint.

    Attributes:
        metric: The metric that was checked
        passed: Whether the constraint passed
        actual_value: The actual value observed
        expected_value: The expected value from spec
        reason: Human-readable explanation
    """
    metric: str
    passed: bool
    actual_value: Union[str, int, float, None]
    expected_value: Union[str, int, float, dict]
    reason: str

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "passed": self.passed,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "reason": self.reason
        }


@dataclass(frozen=True)
class CheckResult:
    """
    Complete result of running the checker.

    Attributes:
        scenario_name: Name of the scenario
        passed: Overall pass/fail
        results: Individual constraint results
        metrics_present: Set of metrics that were present
        metrics_missing: Set of metrics that were missing
    """
    scenario_name: str
    passed: bool
    results: tuple[ValidationResult, ...]
    metrics_present: tuple[str, ...]
    metrics_missing: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "passed": self.passed,
            "results": [r.to_dict() for r in self.results],
            "metrics_present": list(self.metrics_present),
            "metrics_missing": list(self.metrics_missing)
        }
