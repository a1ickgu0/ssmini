"""
Semantic IR definitions for OSC DSL.

This module defines the Semantic IR layer which makes scenario meaning explicit.
It transforms the AST into a semantically enriched model.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, Tuple
from enum import Enum

from compiler.ir.ast_nodes import (
    ScenarioNode,
    ActorNode,
    PhaseNode,
    ActionNode,
    ConstraintNode,
    CoverageNode,
    RangeValue,
    DurationValue,
    UntilCondition,
    EventNode,
    OnDirectiveNode,
    EmitNode,
    WaitNode,
    CallNode,
)


class SemanticKind(Enum):
    """Kind of semantic element."""
    SCENARIO = "scenario"
    ACTOR = "actor"
    PHASE = "phase"
    ACTION = "action"
    CONSTRAINT = "constraint"
    COVERAGE = "coverage"
    EVENT = "event"
    ON_DIRECTIVE = "on_directive"
    EMIT = "emit"
    WAIT = "wait"
    CALL = "call"


@dataclass(frozen=True)
class SemanticLocation:
    """Location in the source file."""
    line: int
    column: int
    file: str = "<unknown>"


@dataclass(frozen=True)
class SemanticDuration:
    """Represents a duration in the semantic IR."""
    value: Union[int, float]
    unit: str  # "s", "ms", "us", "m", "h"

    @classmethod
    def from_ast(cls, ast_duration: DurationValue) -> "SemanticDuration":
        """Create SemanticDuration from AST DurationValue."""
        return cls(
            value=ast_duration.value,
            unit=ast_duration.unit.value
        )

    def to_seconds(self) -> float:
        """Convert to seconds."""
        conversions = {"h": 3600, "m": 60, "s": 1, "ms": 0.001, "us": 0.000001}
        return self.value * conversions.get(self.unit, 1)

    def to_dict(self) -> dict:
        return {"value": self.value, "unit": self.unit}


@dataclass(frozen=True)
class SemanticUntilCondition:
    """Represents an until condition in the semantic IR."""
    event_name: Optional[str] = None
    elapsed_time: Optional[SemanticDuration] = None
    expression: Optional[str] = None

    @classmethod
    def from_ast(cls, ast_until: UntilCondition) -> "SemanticUntilCondition":
        """Create SemanticUntilCondition from AST UntilCondition."""
        elapsed = None
        if ast_until.elapsed_time:
            elapsed = SemanticDuration.from_ast(ast_until.elapsed_time)
        return cls(
            event_name=ast_until.event_name,
            elapsed_time=elapsed,
            expression=ast_until.expression
        )

    def to_dict(self) -> dict:
        result = {}
        if self.event_name:
            result["event_name"] = self.event_name
        if self.elapsed_time:
            result["elapsed_time"] = self.elapsed_time.to_dict()
        if self.expression:
            result["expression"] = self.expression
        return result


@dataclass(frozen=True)
class SemanticActor:
    """Represents an actor in the semantic IR."""
    name: str
    actor_type: str
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_actor: ActorNode) -> "SemanticActor":
        """Create SemanticActor from AST ActorNode."""
        return cls(
            name=ast_actor.name,
            actor_type=ast_actor.type,
            location=SemanticLocation(line=0, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        return {
            "type": "SemanticActor",
            "name": self.name,
            "actor_type": self.actor_type,
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }


@dataclass(frozen=True)
class SemanticConstraint:
    """Represents a constraint in the semantic IR."""
    metric: str
    value: Optional[Union[str, int, float, dict]] = None
    anchor: str = "end"  # "start" or "end"
    until: Optional[SemanticUntilCondition] = None
    modifier: Optional[str] = None  # "keep", "hard", "default"
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_constraint: ConstraintNode, line: int = 0) -> "SemanticConstraint":
        """Create SemanticConstraint from AST ConstraintNode."""
        # Convert RangeValue to dict
        value = None
        if ast_constraint.value is not None:
            if isinstance(ast_constraint.value, RangeValue):
                value = {
                    "type": "range",
                    "start": ast_constraint.value.start,
                    "end": ast_constraint.value.end
                }
            else:
                value = ast_constraint.value

        # Convert until condition
        until = None
        if ast_constraint.until:
            until = SemanticUntilCondition.from_ast(ast_constraint.until)

        return cls(
            metric=ast_constraint.metric,
            value=value,
            anchor=ast_constraint.anchor.value if hasattr(ast_constraint.anchor, 'value') else ast_constraint.anchor,
            until=until,
            modifier=ast_constraint.constraint_modifier,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticConstraint",
            "metric": self.metric,
            "anchor": self.anchor
        }
        if self.value is not None:
            result["value"] = self.value
        if self.until:
            result["until"] = self.until.to_dict()
        if self.modifier:
            result["modifier"] = self.modifier
        if self.location:
            result["location"] = {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            }
        return result


@dataclass(frozen=True)
class SemanticAction:
    """Represents an action in the semantic IR."""
    actor: str
    name: str
    constraints: tuple[SemanticConstraint, ...] = field(default_factory=tuple)
    modifiers: tuple[str, ...] = field(default_factory=tuple)
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_action: ActionNode, line: int = 0) -> "SemanticAction":
        """Create SemanticAction from AST ActionNode."""
        constraints = tuple(
            SemanticConstraint.from_ast(c, line=line + i)
            for i, c in enumerate(ast_action.constraints)
        )
        return cls(
            actor=ast_action.actor,
            name=ast_action.name,
            constraints=constraints,
            modifiers=ast_action.modifiers,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticAction",
            "actor": self.actor,
            "name": self.name,
            "constraints": [c.to_dict() for c in self.constraints],
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }
        if self.modifiers:
            result["modifiers"] = list(self.modifiers)
        return result


@dataclass(frozen=True)
class SemanticPhase:
    """Represents a phase with serial, parallel, or one_of execution."""
    name: str
    mode: str  # "serial", "parallel", or "one_of"
    children: tuple[Union["SemanticAction", "SemanticPhase", "SemanticEmit", "SemanticWait", "SemanticCall"], ...] = field(default_factory=tuple)
    duration: Optional[SemanticDuration] = None
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_phase: PhaseNode, line: int = 0) -> "SemanticPhase":
        """Create SemanticPhase from AST PhaseNode."""
        children = []
        for i, child in enumerate(ast_phase.children):
            if isinstance(child, ActionNode):
                children.append(SemanticAction.from_ast(child, line=line + i))
            elif isinstance(child, PhaseNode):
                children.append(SemanticPhase.from_ast(child, line=line + i))
            elif isinstance(child, EmitNode):
                children.append(SemanticEmit.from_ast(child, line=line + i))
            elif isinstance(child, WaitNode):
                children.append(SemanticWait.from_ast(child, line=line + i))
            elif isinstance(child, CallNode):
                children.append(SemanticCall.from_ast(child, line=line + i))

        duration = None
        if ast_phase.duration:
            duration = SemanticDuration.from_ast(ast_phase.duration)

        return cls(
            name=ast_phase.name,
            mode=ast_phase.mode,
            children=tuple(children),
            duration=duration,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticPhase",
            "name": self.name,
            "mode": self.mode,
            "children": [c.to_dict() for c in self.children],
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }
        if self.duration:
            result["duration"] = self.duration.to_dict()
        return result


@dataclass(frozen=True)
class SemanticEvent:
    """Represents an event declaration in the semantic IR."""
    name: str
    condition_type: str  # "elapsed", "rise", "fall", "every", "expression"
    condition_value: Optional[Union[SemanticDuration, str]] = None
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_event: EventNode, line: int = 0) -> "SemanticEvent":
        """Create SemanticEvent from AST EventNode."""
        condition_value = None
        if ast_event.condition_value:
            if isinstance(ast_event.condition_value, DurationValue):
                condition_value = SemanticDuration.from_ast(ast_event.condition_value)
            else:
                condition_value = ast_event.condition_value

        return cls(
            name=ast_event.name,
            condition_type=ast_event.condition_type,
            condition_value=condition_value,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticEvent",
            "name": self.name,
            "condition_type": self.condition_type
        }
        if self.condition_value:
            if isinstance(self.condition_value, SemanticDuration):
                result["condition_value"] = self.condition_value.to_dict()
            else:
                result["condition_value"] = self.condition_value
        if self.location:
            result["location"] = {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            }
        return result


@dataclass(frozen=True)
class SemanticOnDirective:
    """Represents an on directive in the semantic IR."""
    event_name: str
    actions: tuple[Union["SemanticEmit", "SemanticCall", "SemanticAction"], ...] = field(default_factory=tuple)
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_on: OnDirectiveNode, line: int = 0) -> "SemanticOnDirective":
        """Create SemanticOnDirective from AST OnDirectiveNode."""
        actions = []
        for i, child in enumerate(ast_on.actions):
            if isinstance(child, EmitNode):
                actions.append(SemanticEmit.from_ast(child, line=line + i))
            elif isinstance(child, CallNode):
                actions.append(SemanticCall.from_ast(child, line=line + i))
            elif isinstance(child, ActionNode):
                actions.append(SemanticAction.from_ast(child, line=line + i))

        return cls(
            event_name=ast_on.event_name,
            actions=tuple(actions),
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        return {
            "type": "SemanticOnDirective",
            "event_name": self.event_name,
            "actions": [a.to_dict() for a in self.actions],
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }


@dataclass(frozen=True)
class SemanticEmit:
    """Represents an emit directive in the semantic IR."""
    event_name: str
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_emit: EmitNode, line: int = 0) -> "SemanticEmit":
        """Create SemanticEmit from AST EmitNode."""
        return cls(
            event_name=ast_emit.event_name,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        return {
            "type": "SemanticEmit",
            "event_name": self.event_name,
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }


@dataclass(frozen=True)
class SemanticWait:
    """Represents a wait directive in the semantic IR."""
    event_name: Optional[str] = None
    elapsed_time: Optional[SemanticDuration] = None
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_wait: WaitNode, line: int = 0) -> "SemanticWait":
        """Create SemanticWait from AST WaitNode."""
        elapsed = None
        if ast_wait.elapsed_time:
            elapsed = SemanticDuration.from_ast(ast_wait.elapsed_time)

        return cls(
            event_name=ast_wait.event_name,
            elapsed_time=elapsed,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        result = {"type": "SemanticWait"}
        if self.event_name:
            result["event_name"] = self.event_name
        if self.elapsed_time:
            result["elapsed_time"] = self.elapsed_time.to_dict()
        if self.location:
            result["location"] = {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            }
        return result


@dataclass(frozen=True)
class SemanticCall:
    """Represents a call directive in the semantic IR."""
    function_name: str
    arguments: tuple[Union[str, int, float], ...] = field(default_factory=tuple)
    location: Optional[SemanticLocation] = None

    @classmethod
    def from_ast(cls, ast_call: CallNode, line: int = 0) -> "SemanticCall":
        """Create SemanticCall from AST CallNode."""
        return cls(
            function_name=ast_call.function_name,
            arguments=ast_call.arguments,
            location=SemanticLocation(line=line, column=0, file="<scenario>")
        )

    def to_dict(self) -> dict:
        return {
            "type": "SemanticCall",
            "function_name": self.function_name,
            "arguments": list(self.arguments),
            "location": {
                "line": self.location.line,
                "column": self.location.column,
                "file": self.location.file
            } if self.location else None
        }


@dataclass(frozen=True)
class SemanticCoverage:
    """Represents a coverage goal."""
    name: str
    target: Union[str, int, float]
    sampling: str = "event"
    min_samples: int = 1
    max_samples: Optional[int] = None

    @classmethod
    def from_ast(cls, ast_coverage: CoverageNode) -> "SemanticCoverage":
        """Create SemanticCoverage from AST CoverageNode."""
        return cls(
            name=ast_coverage.name,
            target=ast_coverage.target,
            sampling=ast_coverage.sampling,
            min_samples=ast_coverage.min_samples,
            max_samples=ast_coverage.max_samples
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticCoverage",
            "name": self.name,
            "target": self.target,
            "sampling": self.sampling,
            "min_samples": self.min_samples
        }
        if self.max_samples is not None:
            result["max_samples"] = self.max_samples
        return result


@dataclass(frozen=True)
class SemanticScenario:
    """Root of the Semantic IR - makes scenario meaning explicit."""
    name: str
    actors: tuple[SemanticActor, ...] = field(default_factory=tuple)
    events: tuple[SemanticEvent, ...] = field(default_factory=tuple)
    on_directives: tuple[SemanticOnDirective, ...] = field(default_factory=tuple)
    phases: tuple[SemanticPhase, ...] = field(default_factory=tuple)
    coverages: tuple[SemanticCoverage, ...] = field(default_factory=tuple)

    @classmethod
    def from_ast(cls, ast_scenario: ScenarioNode) -> "SemanticScenario":
        """Create SemanticScenario from AST ScenarioNode."""
        actors = tuple(SemanticActor.from_ast(a) for a in ast_scenario.actors)
        events = tuple(SemanticEvent.from_ast(e) for e in ast_scenario.events)
        on_directives = tuple(SemanticOnDirective.from_ast(o) for o in ast_scenario.on_directives)

        phases = tuple()
        if ast_scenario.body:
            phases = (SemanticPhase.from_ast(ast_scenario.body),)

        coverages = tuple(SemanticCoverage.from_ast(c) for c in ast_scenario.coverages)

        return cls(
            name=ast_scenario.name,
            actors=actors,
            events=events,
            on_directives=on_directives,
            phases=phases,
            coverages=coverages
        )

    def to_dict(self) -> dict:
        result = {
            "type": "SemanticScenario",
            "name": self.name,
            "actors": [a.to_dict() for a in self.actors],
            "phases": [p.to_dict() for p in self.phases],
            "coverages": [c.to_dict() for c in self.coverages]
        }
        if self.events:
            result["events"] = [e.to_dict() for e in self.events]
        if self.on_directives:
            result["on_directives"] = [o.to_dict() for o in self.on_directives]
        return result


def to_json(scenario: SemanticScenario) -> dict:
    """Convert SemanticScenario to JSON-compatible dict."""
    return scenario.to_dict()


# Constraint Specification IR - for runtime evaluation

@dataclass(frozen=True)
class ConstraintOperator(str, Enum):
    """Operators for constraint compilation."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_EQ = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQ = ">="
    IN_RANGE = "in"
    NOT_IN_RANGE = "not-in"


@dataclass(frozen=True)
class ConstraintSpec:
    """
    Compiled constraint specification for runtime evaluation.

    Output format:
    {
        "metric": "...",
        "operator": "...",
        "value": "...",
        "anchor": "start/end"
    }
    """
    metric: str
    operator: ConstraintOperator
    value: Union[str, int, float, dict]  # scalar or range dict
    anchor: str  # "start" or "end"

    def to_dict(self) -> dict:
        result = {
            "metric": self.metric,
            "operator": self.operator.value,
            "value": self.value,
            "anchor": self.anchor
        }
        return result

    @classmethod
    def from_semantic(cls, semantic_constraint: "SemanticConstraint") -> "ConstraintSpec":
        """Create ConstraintSpec from SemanticConstraint."""
        metric = semantic_constraint.metric
        value = semantic_constraint.value
        anchor = semantic_constraint.anchor

        # Determine operator based on value type
        if isinstance(value, dict) and value.get("type") == "range":
            # Range constraint
            operator = ConstraintOperator.IN_RANGE
        elif isinstance(value, (int, float)):
            # Equality comparison with number
            operator = ConstraintOperator.EQUALS
        elif isinstance(value, str):
            # Equality comparison with string
            operator = ConstraintOperator.EQUALS
        else:
            # Default to equals
            operator = ConstraintOperator.EQUALS

        return cls(
            metric=metric,
            operator=operator,
            value=value,
            anchor=anchor
        )

    @classmethod
    def from_ast(cls, ast_constraint, line: int = 0) -> "ConstraintSpec":
        """Create ConstraintSpec directly from AST ConstraintNode."""
        # Get value
        value = None
        if ast_constraint.value is not None:
            if isinstance(ast_constraint.value, RangeValue):
                value = {
                    "type": "range",
                    "start": ast_constraint.value.start,
                    "end": ast_constraint.value.end
                }
            else:
                value = ast_constraint.value

        # Determine operator
        if isinstance(ast_constraint.value, RangeValue):
            operator = ConstraintOperator.IN_RANGE
        elif isinstance(ast_constraint.value, (int, float)):
            operator = ConstraintOperator.EQUALS
        elif isinstance(ast_constraint.value, str):
            operator = ConstraintOperator.EQUALS
        else:
            operator = ConstraintOperator.EQUALS

        anchor = ast_constraint.anchor.value if hasattr(ast_constraint.anchor, 'value') else ast_constraint.anchor

        return cls(
            metric=ast_constraint.metric,
            operator=operator,
            value=value,
            anchor=anchor
        )


def compile_constraints(semantic_scenario: SemanticScenario) -> list[ConstraintSpec]:
    """
    Compile all constraints in a SemanticScenario to ConstraintSpec.

    Returns a list of all constraint specifications for runtime evaluation.
    """
    constraint_specs = []

    for phase in semantic_scenario.phases:
        for constraint in _extract_constraints_from_phase(phase):
            constraint_specs.append(ConstraintSpec.from_semantic(constraint))

    return constraint_specs


def _extract_constraints_from_phase(phase: SemanticPhase) -> list[SemanticConstraint]:
    """Recursively extract all constraints from a phase and its children."""
    constraints = []

    for child in phase.children:
        if isinstance(child, SemanticAction):
            constraints.extend(child.constraints)
        elif isinstance(child, SemanticPhase):
            constraints.extend(_extract_constraints_from_phase(child))

    return constraints


def compile_to_json(semantic_scenario: SemanticScenario) -> dict:
    """
    Compile a SemanticScenario to constraint JSON.

    Returns:
        {
            "scenario": "...",
            "constraints": [...]
        }
    """
    constraints = compile_constraints(semantic_scenario)

    return {
        "scenario": semantic_scenario.name,
        "constraints": [c.to_dict() for c in constraints]
    }
