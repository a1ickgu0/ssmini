"""
AST Node definitions for OSC DSL.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Union
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
class ConstraintNode(ASTNode):
    """Represents a constraint in a with: block."""
    metric: str
    value: Optional[Union[str, int, float, RangeValue]] = None
    anchor: AnchorType = AnchorType.END

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


@dataclass(frozen=True)
class PhaseNode(ASTNode):
    """Represents a phase with serial or parallel execution."""
    name: str
    mode: Literal["serial", "parallel"]
    children: tuple[ASTNode, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError("Phase name must be a string")
        if self.mode not in ("serial", "parallel"):
            raise ValueError(f"Phase mode must be 'serial' or 'parallel', got {self.mode}")
        if not isinstance(self.children, tuple):
            object.__setattr__(self, 'children', tuple(self.children))
        for child in self.children:
            if not isinstance(child, ASTNode):
                raise ValueError(f"All children must be ASTNode, got {type(child)}")


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
        return {
            "type": "Scenario",
            "name": node.name,
            "actors": [node_to_dict(a) for a in node.actors],
            "body": node_to_dict(node.body) if node.body else None,
            "coverages": [node_to_dict(c) for c in node.coverages]
        }
    elif isinstance(node, ActorNode):
        return {
            "type": "Actor",
            "name": node.name,
            "actor_type": node.type
        }
    elif isinstance(node, PhaseNode):
        return {
            "type": "Phase",
            "name": node.name,
            "mode": node.mode,
            "children": [node_to_dict(c) for c in node.children]
        }
    elif isinstance(node, ActionNode):
        return {
            "type": "Action",
            "actor": node.actor,
            "name": node.name,
            "constraints": [node_to_dict(c) for c in node.constraints]
        }
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
        return result
    elif isinstance(node, RangeValue):
        return {
            "type": "RangeValue",
            "start": node.start,
            "end": node.end
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
        lines = [f"{prefix}Phase: {node.name} [{node.mode}]"]
        for child in node.children:
            lines.append(print_ast(child, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, ActionNode):
        lines = [f"{prefix}Action: {node.actor}.{node.name}()"]
        for c in node.constraints:
            lines.append(print_ast(c, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, ConstraintNode):
        value_str = node.value
        if isinstance(node.value, RangeValue):
            value_str = f"[{node.value.start}..{node.value.end}]"
        return f"{prefix}Constraint: {node.metric} = {value_str} @ {node.anchor.value if hasattr(node.anchor, 'value') else node.anchor}"
    elif isinstance(node, RangeValue):
        return f"{prefix}Range: [{node.start}..{node.end}]"
    elif isinstance(node, CoverageNode):
        result = f"{prefix}Coverage: {node.name} = {node.target} (sampling={node.sampling}, min={node.min_samples}"
        if node.max_samples is not None:
            result += f", max={node.max_samples}"
        result += ")"
        return result
    return f"{prefix}{node}"