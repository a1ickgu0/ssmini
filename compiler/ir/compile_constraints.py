"""
CLI for constraint compilation.

Compiles Semantic IR constraints to ConstraintSpec IR for runtime evaluation.
"""

import sys
import json
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import (
    SemanticScenario,
    compile_to_json
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compile_constraints.py <osc_file> [output_json]")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # Parse the DSL file
        ast_scenario = parse_file(input_file)

        # Convert AST to Semantic IR
        semantic_ir = SemanticScenario.from_ast(ast_scenario)

        # Compile constraints to IR
        result = compile_to_json(semantic_ir)

        # Print or write to file
        output = json.dumps(result, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Constraint IR written to: {output_file}")
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
