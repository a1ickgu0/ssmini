"""
End-to-End pipeline for OSC DSL compiler.

Runs the full pipeline: DSL -> AST -> Semantic IR -> Execution Plan -> Execute -> Check -> Report

Pipeline stages:
1. Parse DSL to AST
2. Build Semantic IR from AST
3. Map to Execution Plan using bindings
4. Execute with Mock Backend
5. Validate with Checker
6. Generate Final Report
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ValidationStatus(str, Enum):
    """Status of validation."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidationIssue:
    """
    A validation issue (violation or warning).

    Attributes:
        metric: The metric that failed
        expected: Expected value/range
        actual: Actual value observed
        severity: "error" or "warning"
        description: Human-readable description
    """
    metric: str
    expected: str
    actual: str
    severity: str
    description: str

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity,
            "description": self.description
        }


@dataclass(frozen=True)
class ExecutionMetrics:
    """
    Metrics collected during execution.

    Attributes:
        operation: Backend operation name
        duration_ms: Execution duration
        outputs: Output metrics from the operation
    """
    operation: str
    duration_ms: float
    outputs: dict

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "outputs": self.outputs
        }


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result of executing a scenario.

    Attributes:
        scenario_name: Name of the scenario
        status: Overall execution status
        steps: List of execution steps with metrics
        violations: List of constraint violations
        all_passed: Whether all constraints passed
    """
    scenario_name: str
    status: ValidationStatus
    steps: tuple[ExecutionMetrics, ...]
    violations: tuple[ValidationIssue, ...]
    all_passed: bool

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "status": self.status.value,
            "all_passed": self.all_passed,
            "steps": [s.to_dict() for s in self.steps],
            "violations": [v.to_dict() for v in self.violations]
        }


class E2EPipelineResult:
    """
    Complete result of running the E2E pipeline.
    """

    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.steps = []
        self.violations = []
        self.all_passed = True

    def add_step(self, operation: str, duration_ms: float, outputs: dict):
        """Add an execution step."""
        self.steps.append(ExecutionMetrics(operation, duration_ms, outputs))

    def add_violation(self, issue: ValidationIssue):
        """Add a validation violation."""
        self.violations.append(issue)
        if issue.severity == "error":
            self.all_passed = False

    def set_status(self, status: ValidationStatus):
        """Set the overall status."""
        self.status = status

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "status": self.status.value if hasattr(self, 'status') else "unknown",
            "all_passed": self.all_passed,
            "steps": [s.to_dict() for s in self.steps],
            "violations": [v.to_dict() for v in self.violations]
        }
