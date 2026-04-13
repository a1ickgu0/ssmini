"""
Execution IR for OSC DSL compiler.

Defines the execution plan representation with phases, tasks, and
backend-neutral operations ready for execution by any backend.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from enum import Enum


class ExecutionMode(str, Enum):
    """Execution mode for a phase."""
    SERIAL = "serial"
    PARALLEL = "parallel"


class TaskType(str, Enum):
    """Type of execution task."""
    BACKEND_OPERATION = "backend_operation"
    WAIT = "wait"
    CONDITION_CHECK = "condition_check"
    ASSERTION = "assertion"


@dataclass(frozen=True)
class BackendOperation:
    """
    A backend-neutral operation to execute.

    Attributes:
        name: Operation name (mapped from DSL action)
        inputs: Input parameters (key-value pairs)
        outputs: Expected output metrics
        actor: The actor performing this operation
    """
    name: str
    inputs: dict[str, str]
    outputs: list[str]
    actor: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "actor": self.actor
        }


@dataclass(frozen=True)
class WaitTask:
    """
    A wait/delay task.

    Attributes:
        duration_ms: Duration to wait in milliseconds
        description: Human-readable description
    """
    duration_ms: int
    description: str = ""

    def to_dict(self) -> dict:
        result = {"type": "wait", "duration_ms": self.duration_ms}
        if self.description:
            result["description"] = self.description
        return result


@dataclass(frozen=True)
class ConditionCheck:
    """
    A condition check task.

    Attributes:
        metric: The metric to check
        expected: Expected value
        operator: Comparison operator
        description: Human-readable description
    """
    metric: str
    expected: Union[str, int, float, dict]
    operator: str = "=="
    description: str = ""

    def to_dict(self) -> dict:
        result = {
            "type": "condition_check",
            "metric": self.metric,
            "expected": self.expected,
            "operator": self.operator
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass(frozen=True)
class AssertTask:
    """
    An assertion task that fails the execution if not met.

    Attributes:
        condition: The condition to assert
        description: Human-readable description
    """
    condition: str
    description: str = ""

    def to_dict(self) -> dict:
        result = {"type": "assertion", "condition": self.condition}
        if self.description:
            result["description"] = self.description
        return result


# Union type for all task types
ExecutionTask = Union[BackendOperation, WaitTask, ConditionCheck, AssertTask]


@dataclass(frozen=True)
class ExecutionPhase:
    """
    An execution phase containing tasks.

    Attributes:
        name: Phase name
        mode: Serial or parallel execution
        tasks: List of tasks to execute
        description: Human-readable description
    """
    name: str
    mode: ExecutionMode
    tasks: tuple[ExecutionTask, ...]
    description: str = ""

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "mode": self.mode.value,
            "tasks": [t.to_dict() for t in self.tasks]
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass(frozen=True)
class AcceptanceRule:
    """
    An acceptance rule for the scenario.

    Attributes:
        metric: The metric to check
        constraint: The constraint specification
        description: Human-readable description
    """
    metric: str
    constraint: dict
    description: str = ""

    def to_dict(self) -> dict:
        result = {
            "metric": self.metric,
            "constraint": self.constraint
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Complete execution plan ready for backend execution.

    Attributes:
        scenario_name: Name of the scenario
        phases: List of execution phases
        acceptance_rules: List of acceptance rules
        coverage_specs: Coverage specifications
        actors: List of actors involved
    """
    scenario_name: str
    phases: tuple[ExecutionPhase, ...]
    acceptance_rules: tuple[AcceptanceRule, ...] = field(default_factory=tuple)
    coverage_specs: dict = field(default_factory=dict)
    actors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "phases": [p.to_dict() for p in self.phases],
            "acceptance_rules": [r.to_dict() for r in self.acceptance_rules],
            "coverage_specs": self.coverage_specs,
            "actors": list(self.actors)
        }


@dataclass(frozen=True)
class ExecutionPlanBuilder:
    """
    Builder for constructing execution plans.

    Provides fluent API for building execution plans step by step.
    """

    _scenario_name: str = ""
    _phases: list[ExecutionPhase] = field(default_factory=list)
    _acceptance_rules: list[AcceptanceRule] = field(default_factory=list)
    _coverage_specs: dict = field(default_factory=dict)
    _actors: list[str] = field(default_factory=list)

    @classmethod
    def for_scenario(cls, name: str) -> "ExecutionPlanBuilder":
        return cls(_scenario_name=name)

    def add_phase(self, phase: ExecutionPhase) -> "ExecutionPlanBuilder":
        self._phases.append(phase)
        return self

    def add_phases(self, phases: list[ExecutionPhase]) -> "ExecutionPlanBuilder":
        self._phases.extend(phases)
        return self

    def add_acceptance_rule(self, rule: AcceptanceRule) -> "ExecutionPlanBuilder":
        self._acceptance_rules.append(rule)
        return self

    def set_coverage(self, specs: dict) -> "ExecutionPlanBuilder":
        self._coverage_specs = specs
        return self

    def add_actor(self, actor: str) -> "ExecutionPlanBuilder":
        if actor not in self._actors:
            self._actors.append(actor)
        return self

    def build(self) -> ExecutionPlan:
        return ExecutionPlan(
            scenario_name=self._scenario_name,
            phases=tuple(self._phases),
            acceptance_rules=tuple(self._acceptance_rules),
            coverage_specs=self._coverage_specs,
            actors=tuple(self._actors)
        )
