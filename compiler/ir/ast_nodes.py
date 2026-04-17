"""
AST Node definitions for OSC DSL.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Union, Tuple
from enum import Enum


class AnchorType(str, Enum):
    """Anchor types for constraints."""
    START = "start"
    END = "end"


class ValueType(str, Enum):
    """Value types for constraint values."""
    RANGE = "range"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"


class DurationUnit(str, Enum):
    """Duration units for time specifications."""
    S = "s"
    MS = "ms"
    US = "us"
    M = "m"
    H = "h"


@dataclass(frozen=True)
class DurationValue:
    """Represents a duration with unit, e.g., 30s, 100ms."""
    value: Union[int, float]
    unit: DurationUnit = DurationUnit.S

    def to_seconds(self) -> float:
        """Convert duration to seconds."""
        conversions = {
            DurationUnit.H: 3600,
            DurationUnit.M: 60,
            DurationUnit.S: 1,
            DurationUnit.MS: 0.001,
            DurationUnit.US: 0.000001,
        }
        return self.value * conversions[self.unit]


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""
    pass


@dataclass(frozen=True)
class RangeValue:
    """Represents a range value like [-67..-55]."""
    start: Union[int, float]
    end: Union[int, float]

    def __post_init__(self):
        if not isinstance(self.start, (int, float)):
            raise ValueError(f"Range start must be numeric, got {type(self.start)}")
        if not isinstance(self.end, (int, float)):
            raise ValueError(f"Range end must be numeric, got {type(self.end)}")
        if self.start > self.end:
            raise ValueError(f"Range start {self.start} must be <= end {self.end}")


@dataclass(frozen=True)
class UntilCondition:
    """Represents an until condition in a with: block."""
    event_name: Optional[str] = None  # @event_name
    elapsed_time: Optional[DurationValue] = None  # elapsed(30s)
    expression: Optional[str] = None  # condition expression

    def __post_init__(self):
        if self.event_name is None and self.elapsed_time is None and self.expression is None:
            raise ValueError("UntilCondition must have at least one condition")


@dataclass(frozen=True)
class ConstraintNode(ASTNode):
    """Represents a constraint in a with: block."""
    metric: str
    value: Optional[Union[str, int, float, RangeValue]] = None
    anchor: AnchorType = AnchorType.END
    until: Optional[UntilCondition] = None  # until directive
    constraint_modifier: Optional[Literal["keep", "hard", "default"]] = None

    def __post_init__(self):
        if not isinstance(self.metric, str) or not self.metric:
            raise ValueError("Constraint metric must be a non-empty string")
        if self.value is not None:
            valid_types = (str, int, float, RangeValue)
            if not isinstance(self.value, valid_types):
                raise ValueError(f"Constraint value must be str|int|float|RangeValue, got {type(self.value)}")
        if not isinstance(self.anchor, AnchorType):
            raise ValueError(f"Constraint anchor must be AnchorType, got {self.anchor}")


@dataclass(frozen=True)
class ActionNode(ASTNode):
    """Represents an action invocation."""
    actor: str
    name: str
    constraints: tuple[ConstraintNode, ...] = field(default_factory=tuple)
    modifiers: tuple[str, ...] = field(default_factory=tuple)  # modifier applications

    def __post_init__(self):
        if not isinstance(self.actor, str) or not self.actor:
            raise ValueError("Action actor must be a non-empty string")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Action name must be a non-empty string")
        if not isinstance(self.constraints, tuple):
            object.__setattr__(self, 'constraints', tuple(self.constraints))
        for c in self.constraints:
            if not isinstance(c, ConstraintNode):
                raise ValueError(f"All constraints must be ConstraintNode, got {type(c)}")
        if not isinstance(self.modifiers, tuple):
            object.__setattr__(self, 'modifiers', tuple(self.modifiers))


@dataclass(frozen=True)
class PhaseNode(ASTNode):
    """Represents a phase with serial, parallel, or one_of execution."""
    name: str  # labeled phase name
    mode: Literal["serial", "parallel", "one_of"]
    children: tuple[ASTNode, ...] = field(default_factory=tuple)
    duration: Optional[DurationValue] = None  # duration parameter

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError("Phase name must be a string")
        if self.mode not in ("serial", "parallel", "one_of"):
            raise ValueError(f"Phase mode must be 'serial', 'parallel', or 'one_of', got {self.mode}")
        if not isinstance(self.children, tuple):
            object.__setattr__(self, 'children', tuple(self.children))
        for child in self.children:
            if not isinstance(child, ASTNode):
                raise ValueError(f"All children must be ASTNode, got {type(child)}")


@dataclass(frozen=True)
class EventNode(ASTNode):
    """Represents an event declaration."""
    name: str
    condition_type: Literal["elapsed", "rise", "fall", "every", "expression"]
    condition_value: Optional[Union[DurationValue, str]] = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Event name must be a non-empty string")
        if self.condition_type not in ("elapsed", "rise", "fall", "every", "expression"):
            raise ValueError(f"Event condition_type must be valid, got {self.condition_type}")


@dataclass(frozen=True)
class OnDirectiveNode(ASTNode):
    """Represents an on @event: directive for event handling."""
    event_name: str
    actions: tuple[ASTNode, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.event_name, str) or not self.event_name:
            raise ValueError("Event name must be a non-empty string")
        if not isinstance(self.actions, tuple):
            object.__setattr__(self, 'actions', tuple(self.actions))


@dataclass(frozen=True)
class EmitNode(ASTNode):
    """Represents an emit directive for event emission."""
    event_name: str

    def __post_init__(self):
        if not isinstance(self.event_name, str) or not self.event_name:
            raise ValueError("Event name must be a non-empty string")


@dataclass(frozen=True)
class WaitNode(ASTNode):
    """Represents a wait directive for event waiting."""
    event_name: Optional[str] = None
    elapsed_time: Optional[DurationValue] = None

    def __post_init__(self):
        if self.event_name is None and self.elapsed_time is None:
            raise ValueError("WaitNode must have either event_name or elapsed_time")


@dataclass(frozen=True)
class CallNode(ASTNode):
    """Represents a call directive for function invocation."""
    function_name: str
    arguments: tuple[Union[str, int, float], ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.function_name, str) or not self.function_name:
            raise ValueError("Function name must be a non-empty string")
        if not isinstance(self.arguments, tuple):
            object.__setattr__(self, 'arguments', tuple(self.arguments))


@dataclass(frozen=True)
class ActorNode(ASTNode):
    """Represents an actor declaration."""
    name: str
    type: str

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Actor name must be a non-empty string")
        if not isinstance(self.type, str) or not self.type:
            raise ValueError("Actor type must be a non-empty string")


@dataclass(frozen=True)
class ScenarioNode(ASTNode):
    """Root node representing a complete scenario."""
    name: str
    actors: tuple[ActorNode, ...] = field(default_factory=tuple)
    events: tuple[EventNode, ...] = field(default_factory=tuple)  # event declarations
    on_directives: tuple[OnDirectiveNode, ...] = field(default_factory=tuple)  # on @event handlers
    body: Optional[PhaseNode] = None
    coverages: tuple[CoverageNode, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Scenario name must be a non-empty string")
        if not isinstance(self.actors, tuple):
            object.__setattr__(self, 'actors', tuple(self.actors))
        for a in self.actors:
            if not isinstance(a, ActorNode):
                raise ValueError(f"All actors must be ActorNode, got {type(a)}")
        if not isinstance(self.events, tuple):
            object.__setattr__(self, 'events', tuple(self.events))
        for e in self.events:
            if not isinstance(e, EventNode):
                raise ValueError(f"All events must be EventNode, got {type(e)}")
        if not isinstance(self.on_directives, tuple):
            object.__setattr__(self, 'on_directives', tuple(self.on_directives))
        for o in self.on_directives:
            if not isinstance(o, OnDirectiveNode):
                raise ValueError(f"All on_directives must be OnDirectiveNode, got {type(o)}")
        if self.body is not None and not isinstance(self.body, PhaseNode):
            raise ValueError(f"Scenario body must be PhaseNode or None, got {type(self.body)}")
        if not isinstance(self.coverages, tuple):
            object.__setattr__(self, 'coverages', tuple(self.coverages))
        for c in self.coverages:
            if not isinstance(c, CoverageNode):
                raise ValueError(f"All coverages must be CoverageNode, got {type(c)}")


@dataclass(frozen=True)
class CoverageNode(ASTNode):
    """Represents a coverage goal."""
    name: str
    target: Union[str, int, float]
    sampling: Literal["interval", "event", "random"] = "event"
    min_samples: int = 1
    max_samples: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Coverage name must be a non-empty string")
        if not isinstance(self.target, (str, int, float)):
            raise ValueError(f"Coverage target must be str|int|float, got {type(self.target)}")
        if self.sampling not in ("interval", "event", "random"):
            raise ValueError(f"Coverage sampling must be 'interval'|'event'|'random', got {self.sampling}")
        if not isinstance(self.min_samples, int) or self.min_samples < 1:
            raise ValueError(f"Coverage min_samples must be >= 1, got {self.min_samples}")
        if self.max_samples is not None and self.max_samples < self.min_samples:
            raise ValueError(f"Coverage max_samples must be >= min_samples, got {self.max_samples} < {self.min_samples}")


def node_to_dict(node: ASTNode) -> dict:
    """Convert AST node to dictionary (for JSON serialization)."""
    if isinstance(node, ScenarioNode):
        result = {
            "type": "Scenario",
            "name": node.name,
            "actors": [node_to_dict(a) for a in node.actors],
            "body": node_to_dict(node.body) if node.body else None,
            "coverages": [node_to_dict(c) for c in node.coverages]
        }
        if node.events:
            result["events"] = [node_to_dict(e) for e in node.events]
        if node.on_directives:
            result["on_directives"] = [node_to_dict(o) for o in node.on_directives]
        return result
    elif isinstance(node, ActorNode):
        return {
            "type": "Actor",
            "name": node.name,
            "actor_type": node.type
        }
    elif isinstance(node, PhaseNode):
        result = {
            "type": "Phase",
            "name": node.name,
            "mode": node.mode,
            "children": [node_to_dict(c) for c in node.children]
        }
        if node.duration:
            result["duration"] = {
                "value": node.duration.value,
                "unit": node.duration.unit.value
            }
        return result
    elif isinstance(node, ActionNode):
        result = {
            "type": "Action",
            "actor": node.actor,
            "name": node.name,
            "constraints": [node_to_dict(c) for c in node.constraints]
        }
        if node.modifiers:
            result["modifiers"] = list(node.modifiers)
        return result
    elif isinstance(node, ConstraintNode):
        result = {
            "type": "Constraint",
            "metric": node.metric,
            "anchor": node.anchor.value if hasattr(node.anchor, 'value') else node.anchor
        }
        # Handle RangeValue serialization
        if isinstance(node.value, RangeValue):
            result["value"] = {
                "type": "range",
                "start": node.value.start,
                "end": node.value.end
            }
        elif node.value is not None:
            result["value"] = node.value
        if node.until:
            result["until"] = {
                "event_name": node.until.event_name,
                "elapsed_time": node.until.elapsed_time.value if node.until.elapsed_time else None,
                "expression": node.until.expression
            }
        if node.constraint_modifier:
            result["modifier"] = node.constraint_modifier
        return result
    elif isinstance(node, EventNode):
        return {
            "type": "Event",
            "name": node.name,
            "condition_type": node.condition_type,
            "condition_value": node.condition_value if not isinstance(node.condition_value, DurationValue)
                              else {"value": node.condition_value.value, "unit": node.condition_value.unit.value}
        }
    elif isinstance(node, OnDirectiveNode):
        return {
            "type": "OnDirective",
            "event_name": node.event_name,
            "actions": [node_to_dict(a) for a in node.actions]
        }
    elif isinstance(node, EmitNode):
        return {
            "type": "Emit",
            "event_name": node.event_name
        }
    elif isinstance(node, WaitNode):
        result = {"type": "Wait"}
        if node.event_name:
            result["event_name"] = node.event_name
        if node.elapsed_time:
            result["elapsed_time"] = {
                "value": node.elapsed_time.value,
                "unit": node.elapsed_time.unit.value
            }
        return result
    elif isinstance(node, CallNode):
        return {
            "type": "Call",
            "function_name": node.function_name,
            "arguments": list(node.arguments)
        }
    elif isinstance(node, RangeValue):
        return {
            "type": "RangeValue",
            "start": node.start,
            "end": node.end
        }
    elif isinstance(node, DurationValue):
        return {
            "type": "DurationValue",
            "value": node.value,
            "unit": node.unit.value
        }
    elif isinstance(node, CoverageNode):
        result = {
            "type": "Coverage",
            "name": node.name,
            "target": node.target,
            "sampling": node.sampling,
            "min_samples": node.min_samples
        }
        if node.max_samples is not None:
            result["max_samples"] = node.max_samples
        return result
    return {"type": str(type(node).__name__)}


def print_ast(node: ASTNode, indent: int = 0) -> str:
    """Print AST in a readable tree format."""
    prefix = "  " * indent
    if isinstance(node, ScenarioNode):
        lines = [f"{prefix}Scenario: {node.name}"]
        lines.append(f"{prefix}  Actors:")
        for a in node.actors:
            lines.append(f"{prefix}    - {a.name}: {a.type}")
        if node.events:
            lines.append(f"{prefix}  Events:")
            for e in node.events:
                lines.append(print_ast(e, indent + 2))
        if node.on_directives:
            lines.append(f"{prefix}  On Directives:")
            for o in node.on_directives:
                lines.append(print_ast(o, indent + 2))
        if node.coverages:
            lines.append(f"{prefix}  Coverages:")
            for c in node.coverages:
                lines.append(print_ast(c, indent + 2))
        if node.body:
            lines.append(f"{prefix}  Body:")
            lines.append(print_ast(node.body, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, ActorNode):
        return f"{prefix}Actor: {node.name} ({node.type})"
    elif isinstance(node, PhaseNode):
        duration_str = ""
        if node.duration:
            duration_str = f" duration={node.duration.value}{node.duration.unit.value}"
        lines = [f"{prefix}Phase: {node.name} [{node.mode}]{duration_str}"]
        for child in node.children:
            lines.append(print_ast(child, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, ActionNode):
        lines = [f"{prefix}Action: {node.actor}.{node.name}()"]
        for c in node.constraints:
            lines.append(print_ast(c, indent + 2))
        if node.modifiers:
            lines.append(f"{prefix}  Modifiers: {', '.join(node.modifiers)}")
        return "\n".join(lines)
    elif isinstance(node, ConstraintNode):
        value_str = node.value
        if isinstance(node.value, RangeValue):
            value_str = f"[{node.value.start}..{node.value.end}]"
        until_str = ""
        if node.until:
            if node.until.event_name:
                until_str = f" until @{node.until.event_name}"
            elif node.until.elapsed_time:
                until_str = f" until elapsed({node.until.elapsed_time.value}{node.until.elapsed_time.unit.value})"
        modifier_str = f" [{node.constraint_modifier}]" if node.constraint_modifier else ""
        return f"{prefix}Constraint{modifier_str}: {node.metric} = {value_str} @ {node.anchor.value if hasattr(node.anchor, 'value') else node.anchor}{until_str}"
    elif isinstance(node, EventNode):
        cond_str = ""
        if node.condition_value:
            if isinstance(node.condition_value, DurationValue):
                cond_str = f"({node.condition_value.value}{node.condition_value.unit.value})"
            else:
                cond_str = f"({node.condition_value})"
        return f"{prefix}Event: {node.name} is {node.condition_type}{cond_str}"
    elif isinstance(node, OnDirectiveNode):
        lines = [f"{prefix}On @{node.event_name}:"]
        for a in node.actions:
            lines.append(print_ast(a, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, EmitNode):
        return f"{prefix}Emit: @{node.event_name}"
    elif isinstance(node, WaitNode):
        if node.event_name:
            return f"{prefix}Wait: @{node.event_name}"
        elif node.elapsed_time:
            return f"{prefix}Wait: elapsed({node.elapsed_time.value}{node.elapsed_time.unit.value})"
        return f"{prefix}Wait: (unknown)"
    elif isinstance(node, CallNode):
        args_str = ", ".join(str(a) for a in node.arguments)
        return f"{prefix}Call: {node.function_name}({args_str})"
    elif isinstance(node, RangeValue):
        return f"{prefix}Range: [{node.start}..{node.end}]"
    elif isinstance(node, DurationValue):
        return f"{prefix}Duration: {node.value}{node.unit.value}"
    elif isinstance(node, CoverageNode):
        result = f"{prefix}Coverage: {node.name} = {node.target} (sampling={node.sampling}, min={node.min_samples}"
        if node.max_samples is not None:
            result += f", max={node.max_samples}"
        result += ")"
        return result
    return f"{prefix}{node}"