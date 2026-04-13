"""
CLI for generating checker specification JSON.

Compiles Semantic IR to constraint validation spec for runtime evaluation.
"""

import sys
import json
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import SemanticScenario, ConstraintSpec as SemanticConstraintSpec
from compiler.ir.ast_nodes import AnchorType


def compile_to_checker_spec(semantic_scenario: SemanticScenario) -> dict:
    """
    Convert a SemanticScenario to a CheckerSpec JSON structure.

    This creates a checker specification that can be used by the runtime
    validator to check execution results.

    Args:
        semantic_scenario: The SemanticScenario to compile

    Returns:
        Dictionary matching checker_spec.json structure
    """
    constraints = []
    metrics_present = set()

    for phase in semantic_scenario.phases:
        for constraint in _extract_constraints_from_phase(phase):
            constraint_dict = {
                "metric": constraint.metric,
                "constraint_type": _get_constraint_type(constraint.value),
                "operator": _get_operator(constraint.value),
                "value": _normalize_value(constraint.value),
                "anchor": constraint.anchor,
                "required": True  # Constraints are required by default
            }
            constraints.append(constraint_dict)
            metrics_present.add(constraint.metric)

    return {
        "scenario_name": semantic_scenario.name,
        "constraints": constraints,
        "accept_on": "all",
        "coverage": {
            "metrics_present": list(metrics_present),
            "metrics_missing": []
        }
    }


def _extract_constraints_from_phase(phase) -> list:
    """Recursively extract all constraints from a phase and its children."""
    constraints = []

    for child in phase.children:
        if isinstance(child, SemanticConstraintSpec):
            constraints.append(child)
        elif hasattr(child, 'constraints'):
            constraints.extend(child.constraints)
        elif hasattr(child, 'children'):
            # Try to get children attribute (for SemanticPhase)
            if hasattr(child, 'children'):
                for c in child.children:
                    if isinstance(c, SemanticConstraintSpec):
                        constraints.append(c)
                    elif hasattr(c, 'constraints'):
                        constraints.extend(c.constraints)

    return constraints


def _get_constraint_type(value) -> str:
    """Determine the constraint type based on the value."""
    if value is None:
        return "presence"
    elif isinstance(value, dict) and value.get("type") == "range":
        return "range"
    else:
        return "equality"


def _get_operator(value) -> str:
    """Determine the operator based on the value type."""
    if value is None:
        return "=="
    elif isinstance(value, dict) and value.get("type") == "range":
        return "in"
    elif isinstance(value, (int, float)):
        return "=="
    elif isinstance(value, str):
        return "=="
    else:
        return "=="


def _normalize_value(value):
    """Normalize the value for the checker spec."""
    if value is None:
        return 0  # For presence checks
    elif isinstance(value, dict) and value.get("type") == "range":
        return {
            "start": value.get("start"),
            "end": value.get("end"),
            "inclusive": True
        }
    else:
        return value


def main():
    if len(sys.argv) < 2:
        print("Usage: python compile_checker_spec.py <osc_file> [output_json]")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # Parse the DSL file
        ast_scenario = parse_file(input_file)

        # Convert AST to Semantic IR
        semantic_ir = SemanticScenario.from_ast(ast_scenario)

        # Compile to checker spec
        result = compile_to_checker_spec(semantic_ir)

        # Output
        output = json.dumps(result, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Checker spec written to: {output_file}")
        else:
            print(output)

        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
