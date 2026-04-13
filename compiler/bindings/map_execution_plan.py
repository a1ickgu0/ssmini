"""
CLI for execution plan mapping.

Maps semantic IR to backend-ready execution plan using binding configuration.
"""

import sys
import json
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import SemanticScenario
from compiler.bindings.loader import BindingLoader
from compiler.bindings.mapper import ExecutionPlanMapper


def main():
    if len(sys.argv) < 2:
        print("Usage: python map_execution_plan.py <osc_file> [binding_yaml] [output_json]")
        return 1

    osc_file = sys.argv[1]
    binding_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Find default binding file if not specified
    if not binding_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_binding = os.path.join(script_dir, "binding.yaml")
        if os.path.exists(default_binding):
            binding_file = default_binding

    try:
        # Parse the DSL file
        ast_scenario = parse_file(osc_file)

        # Convert AST to Semantic IR
        semantic_ir = SemanticScenario.from_ast(ast_scenario)

        # Load bindings
        loader = BindingLoader()
        if binding_file:
            bindings = loader.load(binding_file)
            print(f"Loaded {len(bindings)} binding entries from {binding_file}")

        # Map to execution plan
        mapper = ExecutionPlanMapper(loader)
        execution_plan = mapper.map_scenario(semantic_ir)

        # Convert to dict and output
        result = execution_plan.to_dict()
        output = json.dumps(result, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Execution plan written to: {output_file}")
        else:
            print(output)

        # Summarize bindings used
        if result.get("bindings_used"):
            print(f"\nBindings used: {', '.join(result['bindings_used'])}")

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
