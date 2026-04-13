"""
CLI for executing scenarios with mock backend.

Generates execution trace JSON from a DSL scenario.
"""

import sys
import json
import os
import time

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import SemanticScenario
from compiler.bindings.loader import BindingLoader
from compiler.bindings.mapper import ExecutionPlanMapper
from compiler.lowering.mock_backend import MockBackend
from compiler.lowering.execution_trace import ExecutionTracer


def execute_scenario(
    execution_plan,
    backend: MockBackend,
    tracer: ExecutionTracer
) -> dict:
    """
    Execute an execution plan using the mock backend.

    Args:
        execution_plan: The MappedExecutionPlan to execute
        backend: MockBackend instance
        tracer: ExecutionTracer for recording execution

    Returns:
        Execution trace as dictionary
    """
    tracer.start()

    # Execute each phase from the execution plan (mapped, not semantic)
    for phase in execution_plan.phases:
        _execute_phase_mapped(phase, backend, tracer)

    tracer.end()

    trace = tracer.to_trace()
    return trace.to_dict()


def _execute_phase_mapped(phase, backend: MockBackend, tracer: ExecutionTracer):
    """Execute a single MappedPhase and its children."""
    for child in phase.children:
        if hasattr(child, 'children'):
            # Nested MappedPhase
            _execute_phase_mapped(child, backend, tracer)
        elif hasattr(child, 'dsl_action'):
            # MappedAction from binding
            _execute_action_mapped(child, backend, tracer)


def _execute_action_mapped(action, backend: MockBackend, tracer: ExecutionTracer):
    """Execute a single MappedAction using the mock backend."""
    # Get the binding by name
    action_name = f"{action.dsl_actor}.{action.dsl_action}"

    # Execute the backend operation
    inputs = {k: v.lstrip('$') for k, v in action.inputs.items()}
    result = backend.execute(action.backend_operation, **inputs)

    tracer.record(
        operation=action.backend_operation,
        inputs=inputs,
        outputs=result.metrics,
        status=result.status.value,
        duration_ms=result.duration_ms
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python execute_scenario.py <osc_file> [output_json] [seed]")
        return 1

    osc_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else None

    try:
        # Parse the DSL file
        ast_scenario = parse_file(osc_file)

        # Convert to Semantic IR
        semantic_ir = SemanticScenario.from_ast(ast_scenario)

        # Load bindings
        script_dir = os.path.dirname(os.path.abspath(__file__))
        binding_path = os.path.join(script_dir, "binding.yaml")
        if not os.path.exists(binding_path):
            binding_path = os.path.join(script_dir, "..", "bindings", "binding.yaml")

        loader = BindingLoader()
        loader.load(binding_path)

        # Map to execution plan
        mapper = ExecutionPlanMapper(loader)
        execution_plan = mapper.map_scenario(semantic_ir)

        # Execute with mock backend
        backend = MockBackend(seed=seed)
        # Create a fresh tracer for this execution
        result = execute_scenario(execution_plan, backend, ExecutionTracer(execution_plan.scenario_name))

        # Output
        output = json.dumps(result, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Execution trace written to: {output_file}")
        else:
            print(output)

        # Summary
        total_duration = result.get("total_duration_ms", 0)
        step_count = len(result.get("steps", []))
        print(f"\nExecution summary:")
        print(f"  Steps: {step_count}")
        print(f"  Total duration: {total_duration:.2f}ms")

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
