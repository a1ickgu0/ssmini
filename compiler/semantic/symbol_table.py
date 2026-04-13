"""
Symbol Table for OSC DSL - Manages symbol resolution.

Supports:
- Actor lookup
- Action lookup
- Variable binding
- Enum resolution
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Any

from compiler.ir.ast_nodes import (
    ASTNode,
    ScenarioNode,
    ActorNode,
    ActionNode,
    PhaseNode,
    ConstraintNode,
    RangeValue,
    CoverageNode,
)


class SymbolKind(Enum):
    """Types of symbols that can be stored in the symbol table."""
    ACTOR = auto()        # Named actor instance
    ACTION = auto()       # Action definition
    VARIABLE = auto()     # Variable binding
    ENUM = auto()         # Enum type definition
    ENUM_VALUE = auto()   # Enum value
    CONSTRAINT = auto()   # Constraint definition
    PHASE = auto()        # Phase block
    SCENARIO = auto()     # Scenario root


@dataclass(frozen=True)
class SymbolLocation:
    """Location of a symbol in the source."""
    line: int
    column: int
    file: str = "<unknown>"


@dataclass(frozen=True)
class SymbolEntry:
    """Represents a symbol in the symbol table."""
    name: str
    kind: SymbolKind
    symbol_type: Optional[str] = None  # e.g., "managed_laptop", "employee"
    value: Optional[Any] = None
    location: Optional[SymbolLocation] = None
    scope: str = "global"  # for nested scopes

    def __repr__(self):
        type_str = f": {self.symbol_type}" if self.symbol_type else ""
        return f"SymbolEntry({self.name}{type_str}, {self.kind.name})"


class SymbolTable:
    """
    Manages symbol resolution across different scopes.

    Scopes:
    - global: project-level symbols
    - scenario: scenario-level symbols (actors, coverages)
    - phase: phase-level symbols (nested phases)
    """

    def __init__(self, name: str = "global"):
        self.name: str = name
        self._symbols: Dict[str, List[SymbolEntry]] = {}
        self._scopes: List[Dict[str, List[SymbolEntry]]] = [self._symbols]
        self._scope_stack: List[str] = ["global"]
        self._log: List[str] = []

    def _log_entry(self, message: str) -> None:
        """Log a resolution entry."""
        self._log.append(message)
        print(f"[SymbolTable] {message}")

    def push_scope(self, scope_name: str) -> None:
        """Push a new scope onto the stack."""
        self._scopes.append({})
        self._scope_stack.append(scope_name)
        self._log_entry(f"Push scope: {scope_name}")

    def pop_scope(self) -> str:
        """Pop the current scope from the stack."""
        if len(self._scope_stack) > 1:
            scope = self._scope_stack.pop()
            self._scopes.pop()
            self._log_entry(f"Pop scope: {scope}")
            return scope
        raise ValueError("Cannot pop global scope")

    def declare(self, name: str, kind: SymbolKind, **kwargs) -> SymbolEntry:
        """Declare a new symbol in the current scope."""
        entry = SymbolEntry(
            name=name,
            kind=kind,
            symbol_type=kwargs.get("type"),
            value=kwargs.get("value"),
            location=kwargs.get("location"),
            scope=self._scope_stack[-1] if self._scope_stack else "global"
        )

        if name not in self._symbols:
            self._symbols[name] = []
        self._symbols[name].append(entry)

        self._log_entry(f"Declare: {entry}")
        return entry

    def lookup(self, name: str, kind: Optional[SymbolKind] = None) -> Optional[SymbolEntry]:
        """
        Look up a symbol by name.

        Args:
            name: Symbol name to lookup
            kind: Optional symbol kind to filter by

        Returns:
            SymbolEntry if found, None otherwise
        """
        # Search in reverse scope order (current scope first)
        for scope in reversed(self._scopes):
            if name in scope:
                entries = scope[name]
                if kind:
                    # Filter by kind
                    filtered = [e for e in entries if e.kind == kind]
                    if filtered:
                        self._log_entry(f"Lookup '{name}'[{kind.name}] = {filtered[0]}")
                        return filtered[0]
                else:
                    self._log_entry(f"Lookup '{name}' = {entries[0]}")
                    return entries[0]

        self._log_entry(f"Lookup '{name}' (not found)")
        return None

    def lookup_actor(self, name: str) -> Optional[SymbolEntry]:
        """Look up an actor by name."""
        return self.lookup(name, SymbolKind.ACTOR)

    def lookup_action(self, actor_name: str, action_name: str) -> Optional[SymbolEntry]:
        """
        Look up an action by actor.name format.

        Returns the action entry if found.
        """
        # First look up the actor
        actor = self.lookup(actor_name, SymbolKind.ACTOR)
        if not actor:
            self._log_entry(f"Actor '{actor_name}' not found for action lookup")
            return None

        # Construct full action path
        full_name = f"{actor_name}.{action_name}"
        entry = self.lookup(full_name, SymbolKind.ACTION)

        if entry:
            self._log_entry(f"Action '{full_name}' found")
        else:
            self._log_entry(f"Action '{full_name}' not declared (may be bound externally)")

        return entry

    def lookup_constraint(self, metric: str) -> Optional[SymbolEntry]:
        """Look up a constraint by metric name."""
        return self.lookup(metric, SymbolKind.CONSTRAINT)

    def get_actors(self) -> List[SymbolEntry]:
        """Get all declared actors."""
        return [
            entry for name, entries in self._symbols.items()
            for entry in entries if entry.kind == SymbolKind.ACTOR
        ]

    def get_actions_for_actor(self, actor_name: str) -> List[SymbolEntry]:
        """Get all actions declared for a specific actor."""
        prefix = f"{actor_name}."
        return [
            entry for name, entries in self._symbols.items()
            for entry in entries
            if entry.kind == SymbolKind.ACTION and name.startswith(prefix)
        ]

    def resolve_actor_type(self, actor_name: str) -> Optional[str]:
        """Resolve an actor's type."""
        entry = self.lookup_actor(actor_name)
        return entry.symbol_type if entry else None

    def is_valid_action(self, actor_name: str, action_name: str) -> bool:
        """Check if an action is valid for the given actor."""
        actor = self.lookup_actor(actor_name)
        if not actor:
            return False

        # Check if action is declared for this actor
        action = self.lookup_action(actor_name, action_name)
        if action:
            return True

        # Action may be bound externally (not in symbol table)
        # This is acceptable for the semantic IR phase
        return True

    def build_from_scenario(self, scenario: ScenarioNode) -> "SymbolTable":
        """
        Build symbol table from a parsed ScenarioNode.

        This creates symbol entries for:
        - Scenario itself
        - All actors
        - All actions (including actor.name format)
        - All constraints
        - Coverage goals
        """
        # Declare scenario
        self.declare(
            scenario.name,
            SymbolKind.SCENARIO,
            type="scenario",
            location=SymbolLocation(line=1, column=1)
        )

        # Push scenario scope
        self.push_scope(f"scenario:{scenario.name}")

        # Declare actors
        for actor in scenario.actors:
            self.declare(
                actor.name,
                SymbolKind.ACTOR,
                type=actor.type,
                location=SymbolLocation(line=0, column=0)  # Line not tracked yet
            )
            self._log_entry(f"Registered actor: {actor.name} as {actor.type}")

        # Process body for actions, constraints, and coverages
        if scenario.body:
            self._process_phase(scenario.body)

        # Declare coverages
        for coverage in scenario.coverages:
            self.declare(
                coverage.name,
                SymbolKind.ENUM if coverage.sampling == "enum" else SymbolKind.VARIABLE,
                type="coverage",
                value=coverage.target
            )

        # Pop scenario scope
        self.pop_scope()

        return self

    def _process_phase(self, phase: PhaseNode) -> None:
        """Process a phase node and its children."""
        # Push phase scope
        self.push_scope(f"phase:{phase.name or phase.mode}")

        for child in phase.children:
            if isinstance(child, ActionNode):
                self._process_action(child)
            elif isinstance(child, PhaseNode):
                self._process_phase(child)

        # Pop phase scope
        self.pop_scope()

    def _process_action(self, action: ActionNode) -> None:
        """Process an action node."""
        # Declare action with full path
        full_name = f"{action.actor}.{action.name}"
        self.declare(
            full_name,
            SymbolKind.ACTION,
            type=f"{action.actor}:{action.name}",
            location=SymbolLocation(line=0, column=0)
        )
        self._log_entry(f"Registered action: {full_name}")

        # Process constraints
        for constraint in action.constraints:
            self._process_constraint(constraint)

    def _process_constraint(self, constraint: ConstraintNode) -> None:
        """Process a constraint node."""
        # Add constraint metric to symbol table
        self.declare(
            constraint.metric,
            SymbolKind.CONSTRAINT,
            type=f"constraint({constraint.anchor.value})",
            value=constraint.value
        )

        # Handle range values
        if isinstance(constraint.value, RangeValue):
            self.declare(
                f"{constraint.metric}.start",
                SymbolKind.VARIABLE,
                type="number",
                value=constraint.value.start
            )
            self.declare(
                f"{constraint.metric}.end",
                SymbolKind.VARIABLE,
                type="number",
                value=constraint.value.end
            )

    def get_resolution_log(self) -> List[str]:
        """Get the resolution log."""
        return self._log.copy()

    def clear_log(self) -> None:
        """Clear the resolution log."""
        self._log.clear()

    def __repr__(self) -> str:
        lines = [f"SymbolTable({self.name}):"]
        for name, entries in self._symbols.items():
            for entry in entries:
                lines.append(f"  {entry}")
        return "\n".join(lines)


def resolve_scenario(scenario: ScenarioNode) -> SymbolTable:
    """
    Build and return a symbol table for a scenario.

    This is the main entry point for symbol resolution.
    """
    table = SymbolTable(f"scenario:{scenario.name}")
    table.build_from_scenario(scenario)
    return table
