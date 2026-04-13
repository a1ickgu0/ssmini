"""
Execution plan mapper for OSC DSL compiler.

Maps semantic IR actions to backend operations using binding configuration.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from compiler.ir.semantic_ir import (
    SemanticScenario,
    SemanticAction,
    SemanticPhase,
    SemanticActor,
    SemanticConstraint,
    SemanticCoverage,
)
from compiler.bindings.loader import BindingLoader, BindingEntry


class ExecutionMode(str, Enum):
    """Execution mode for a task."""
    SERIAL = "serial"
    PARALLEL = "parallel"


@dataclass(frozen=True)
class MappedAction:
    """
    Represents an action mapped to a backend operation.

    Attributes:
        dsl_actor: The DSL actor name (e.g., "laptop")
        dsl_action: The DSL action name (e.g., "scan_ssid")
        backend_operation: The backend operation (e.g., "wifi.scan")
        inputs: Mapped input parameters
        outputs: Mapped output metrics
        constraints: Original constraints for validation
    """
    dsl_actor: str
    dsl_action: str
    backend_operation: str
    inputs: dict[str, str]
    outputs: list[str]
    constraints: tuple[SemanticConstraint, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "dsl_actor": self.dsl_actor,
            "dsl_action": self.dsl_action,
            "backend_operation": self.backend_operation,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "constraints": [c.to_dict() for c in self.constraints]
        }


@dataclass(frozen=True)
class MappedPhase:
    """
    Represents a mapped phase with backend operations.

    Attributes:
        name: Phase name
        mode: Execution mode (serial/parallel)
        children: Mapped actions or sub-phases
    """
    name: str
    mode: ExecutionMode
    children: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mode": self.mode.value,
            "children": [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.children]
        }


@dataclass(frozen=True)
class MappedExecutionPlan:
    """
    The fully mapped execution plan ready for backend execution.

    Attributes:
        scenario_name: Name of the scenario
        actors: List of actors involved
        phases: Mapped phases with backend operations
        constraints: All constraints for validation
        coverages: Coverage goals
        bindings_used: List of binding keys used
    """
    scenario_name: str
    actors: tuple[SemanticActor, ...]
    phases: tuple[MappedPhase, ...]
    constraints: tuple[SemanticConstraint, ...]
    coverages: tuple[SemanticCoverage, ...]
    bindings_used: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "actors": [a.to_dict() for a in self.actors],
            "phases": [p.to_dict() for p in self.phases],
            "constraints": [c.to_dict() for c in self.constraints],
            "coverages": [c.to_dict() for c in self.coverages],
            "bindings_used": list(self.bindings_used)
        }


class ExecutionPlanMapper:
    """
    Maps semantic IR to backend-ready execution plan using bindings.
    """

    def __init__(self, binding_loader: BindingLoader):
        """
        Initialize the mapper with binding configuration.

        Args:
            binding_loader: Loaded BindingLoader with binding.yaml configured
        """
        self._loader = binding_loader

    def map_scenario(self, semantic_scenario: SemanticScenario) -> MappedExecutionPlan:
        """
        Map a semantic scenario to a backend execution plan.

        Args:
            semantic_scenario: The semantic IR scenario to map

        Returns:
            MappedExecutionPlan with backend operations
        """
        phases = tuple(
            self._map_phase(p)
            for p in semantic_scenario.phases
        )

        constraints = self._extract_all_constraints(semantic_scenario.phases)
        bindings_used = self._extract_used_bindings(semantic_scenario.phases)

        return MappedExecutionPlan(
            scenario_name=semantic_scenario.name,
            actors=semantic_scenario.actors,
            phases=phases,
            constraints=constraints,
            coverages=semantic_scenario.coverages,
            bindings_used=bindings_used
        )

    def _map_phase(self, semantic_phase: SemanticPhase) -> MappedPhase:
        """Map a single phase and its children."""
        mapped_children = []
        for child in semantic_phase.children:
            if isinstance(child, SemanticAction):
                mapped = self._map_action(child)
                mapped_children.append(mapped)
            elif isinstance(child, SemanticPhase):
                mapped = self._map_phase(child)
                mapped_children.append(mapped)

        return MappedPhase(
            name=semantic_phase.name,
            mode=ExecutionMode(semantic_phase.mode),
            children=tuple(mapped_children)
        )

    def _map_action(self, semantic_action: SemanticAction) -> MappedAction:
        """Map a single action to a backend operation."""
        dsl_action_name = f"{semantic_action.actor}.{semantic_action.name}"
        binding = self._loader.get_binding(dsl_action_name)

        if binding:
            backend_op = binding.backend_operation
            inputs = {p: f"${p}" for p in binding.inputs}
            outputs = list(binding.outputs)
        else:
            # Fallback: use action name as-is if no binding found
            backend_op = semantic_action.name
            inputs = {}
            outputs = []

        return MappedAction(
            dsl_actor=semantic_action.actor,
            dsl_action=semantic_action.name,
            backend_operation=backend_op,
            inputs=inputs,
            outputs=outputs,
            constraints=semantic_action.constraints
        )

    def _extract_all_constraints(self, phases: tuple[SemanticPhase, ...]) -> tuple[SemanticConstraint, ...]:
        """Extract all constraints from phases."""
        constraints = []

        def collect_from_phase(phase: SemanticPhase):
            for child in phase.children:
                if isinstance(child, SemanticAction):
                    constraints.extend(child.constraints)
                elif isinstance(child, SemanticPhase):
                    collect_from_phase(child)

        for phase in phases:
            collect_from_phase(phase)

        return tuple(constraints)

    def _extract_used_bindings(self, phases: tuple[SemanticPhase, ...]) -> tuple[str, ...]:
        """Extract the binding keys used in the scenario."""
        bindings_used = set()

        def collect_from_phase(phase: SemanticPhase):
            for child in phase.children:
                if isinstance(child, SemanticAction):
                    dsl_action = f"{child.actor}.{child.name}"
                    if self._loader.has_binding(dsl_action):
                        bindings_used.add(dsl_action)
                elif isinstance(child, SemanticPhase):
                    collect_from_phase(child)

        for phase in phases:
            collect_from_phase(phase)

        return tuple(sorted(bindings_used))
