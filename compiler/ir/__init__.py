"""
Intermediate Representations module for OSC DSL compiler.

Defines all IR layers:
- Syntax IR (optional, near AST)
- Semantic IR (scenario structure, actors, actions, constraints)
- Execution IR (phases, tasks, operations, acceptance rules)
"""

from compiler.ir.ast_nodes import (
    ScenarioNode,
    ActorNode,
    PhaseNode,
    ActionNode,
    ConstraintNode,
    CoverageNode,
    RangeValue,
    AnchorType,
)
from compiler.ir.semantic_ir import (
    SemanticScenario,
    SemanticActor,
    SemanticPhase,
    SemanticAction,
    SemanticConstraint,
    SemanticCoverage,
    ConstraintSpec,
    ConstraintOperator,
    compile_to_json,
)
from compiler.ir.execution_ir import (
    ExecutionMode,
    TaskType,
    BackendOperation,
    WaitTask,
    ConditionCheck,
    AssertTask,
    ExecutionTask,
    ExecutionPhase,
    AcceptanceRule,
    ExecutionPlan,
    ExecutionPlanBuilder,
)

__all__ = [
    # AST nodes
    "ScenarioNode",
    "ActorNode",
    "PhaseNode",
    "ActionNode",
    "ConstraintNode",
    "CoverageNode",
    "RangeValue",
    "AnchorType",
    # Semantic IR
    "SemanticScenario",
    "SemanticActor",
    "SemanticPhase",
    "SemanticAction",
    "SemanticConstraint",
    "SemanticCoverage",
    "ConstraintSpec",
    "ConstraintOperator",
    "compile_to_json",
    # Execution IR
    "ExecutionMode",
    "TaskType",
    "BackendOperation",
    "WaitTask",
    "ConditionCheck",
    "AssertTask",
    "ExecutionTask",
    "ExecutionPhase",
    "AcceptanceRule",
    "ExecutionPlan",
    "ExecutionPlanBuilder",
]
