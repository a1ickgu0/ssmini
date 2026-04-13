"""
CLI for generating execution plan JSON.

Converts Semantic IR to Execution Plan IR for backend execution.
"""

import sys
import json
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import SemanticScenario
from compiler.bindings.loader import BindingLoader
from compiler.ir.execution_ir import (
    ExecutionPlanBuilder,
    ExecutionPhase,
    ExecutionMode,
    BackendOperation,
    AcceptanceRule,
)


def build_execution_plan(
    semantic_scenario: SemanticScenario,
    binding_loader: BindingLoader
) -> dict:
    """
    Build an execution plan from semantic IR and bindings.

    Args:
        semantic_scenario: The SemanticScenario to convert
        binding_loader: Loaded BindingLoader for action mappings

    Returns:
        Execution plan as dictionary (JSON-compatible)
    """
    builder = ExecutionPlanBuilder.for_scenario(semantic_scenario.name)

    # Add actors
    for actor in semantic_scenario.actors:
        builder.add_actor(actor.name)

    # Build phases from semantic IR
    phases = []
    for phase in semantic_scenario.phases:
        execution_phase = _build_execution_phase(phase, binding_loader)
        phases.append(execution_phase)

    builder.add_phases(phases)

    # Build acceptance rules from constraints
    rules = _extract_acceptance_rules_from_scenario(semantic_scenario)
    for rule in rules:
        builder.add_acceptance_rule(rule)

    # Build final plan
    plan = builder.build()
    return plan.to_dict()


def _build_execution_phase(
    semantic_phase,
    binding_loader: BindingLoader
) -> ExecutionPhase:
    """Convert a SemanticPhase to ExecutionPhase."""
    tasks = []

    for child in semantic_phase.children:
        task = _build_task(child, binding_loader)
        if task:
            if isinstance(task, list):
                # Nested tasks from recursive phase processing
                tasks.extend(task)
            else:
                tasks.append(task)

    return ExecutionPhase(
        name=semantic_phase.name,
        mode=ExecutionMode(semantic_phase.mode),
        tasks=tuple(tasks)
    )


def _build_task(
    child,
    binding_loader: BindingLoader
) -> Optional[BackendOperation]:
    """Convert a semantic child to an execution task."""
    # Check if it's an action
    if hasattr(child, 'actor') and hasattr(child, 'name'):
        # This is a SemanticAction
        action_name = f"{child.actor}.{child.name}"
        binding = binding_loader.get_binding(action_name)

        if binding:
            # Create backend operation from binding
            # binding.inputs is a tuple of input parameter names
            inputs = {param: f"${param}" for param in binding.inputs}
            return BackendOperation(
                name=binding.backend_operation,
                inputs=inputs,
                outputs=list(binding.outputs),
                actor=child.actor
            )

        # Fallback: use action name directly
        return BackendOperation(
            name=child.name,
            inputs={},
            outputs=[],
            actor=child.actor
        )

    # Check if it's a phase (recursively build)
    elif hasattr(child, 'children'):
        # Recursively process nested phases and collect their tasks
        nested_tasks = []
        for grandchild in child.children:
            task = _build_task(grandchild, binding_loader)
            if task:
                nested_tasks.append(task)
        # Return the nested tasks
        return nested_tasks if nested_tasks else None

    return None


def _extract_acceptance_rules(phase) -> list[AcceptanceRule]:
    """Extract acceptance rules from a phase and its children."""
    rules = []

    def collect_from_node(node):
        if hasattr(node, 'constraints'):
            for constraint in node.constraints:
                rule = AcceptanceRule(
                    metric=constraint.metric,
                    constraint={
                        "anchor": constraint.anchor,
                        "value": constraint.value
                    },
                    description=f"Constraint on {constraint.metric} at {constraint.anchor}"
                )
                rules.append(rule)

        if hasattr(node, 'children'):
            for child in node.children:
                collect_from_node(child)

    collect_from_node(phase)
    return rules


def _extract_acceptance_rules_from_scenario(scenario) -> list[AcceptanceRule]:
    """Extract acceptance rules from a semantic scenario."""
    rules = []

    def collect_from_phase(phase):
        if hasattr(phase, 'constraints'):
            for constraint in phase.constraints:
                rule = AcceptanceRule(
                    metric=constraint.metric,
                    constraint={
                        "anchor": constraint.anchor,
                        "value": constraint.value
                    },
                    description=f"Constraint on {constraint.metric} at {constraint.anchor}"
                )
                rules.append(rule)

        if hasattr(phase, 'children'):
            for child in phase.children:
                collect_from_phase(child)

    for phase in scenario.phases:
        collect_from_phase(phase)

    return rules


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_execution_plan.py <osc_file> [output_json]")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # Parse the DSL file
        ast_scenario = parse_file(input_file)

        # Convert AST to Semantic IR
        semantic_ir = SemanticScenario.from_ast(ast_scenario)

        # Load bindings
        script_dir = os.path.dirname(os.path.abspath(__file__))
        binding_path = os.path.join(script_dir, "binding.yaml")
        if not os.path.exists(binding_path):
            binding_path = os.path.join(script_dir, "..", "bindings", "binding.yaml")

        loader = BindingLoader()
        loader.load(binding_path)

        # Build execution plan
        execution_plan = build_execution_plan(semantic_ir, loader)

        # Output
        output = json.dumps(execution_plan, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Execution plan written to: {output_file}")
        else:
            print(output)

        # Summary
        phase_count = len(execution_plan.get("phases", []))
        actor_count = len(execution_plan.get("actors", []))
        print(f"\nExecution plan summary:")
        print(f"  Phases: {phase_count}")
        print(f"  Actors: {actor_count}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
