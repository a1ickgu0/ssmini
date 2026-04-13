"""
CLI for end-to-end scenario execution.

Runs the complete pipeline: DSL -> AST -> Semantic IR -> Execution Plan ->
Execute with Mock Backend -> Check Constraints -> Generate Final Report
"""

import sys
import json
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.parser.parser import parse_file
from compiler.ir.semantic_ir import SemanticScenario, compile_to_json
from compiler.bindings.loader import BindingLoader
from compiler.bindings.mapper import ExecutionPlanMapper
from compiler.lowering.mock_backend import MockBackend
from compiler.lowering.execution_trace import ExecutionTracer
from compiler.runtime.checker_spec import ConstraintSpec, ConstraintType
from compiler.runtime.validator import ConstraintValidator
from compiler.lowering.e2e_pipeline import E2EPipelineResult, ValidationStatus, ValidationIssue


def run_e2e_pipeline(
    dsl_file: str,
    binding_file: str,
    seed: Optional[int] = None,
    verbose: bool = False
) -> dict:
    """
    Run the complete E2E pipeline.

    Args:
        dsl_file: Path to the DSL file
        binding_file: Path to the binding.yaml file
        seed: Random seed for reproducibility
        verbose: Print detailed output

    Returns:
        Final report as dictionary
    """
    if verbose:
        print(f"[*] Loading DSL: {dsl_file}")

    # Stage 1: Parse DSL to AST
    ast_scenario = parse_file(dsl_file)
    if verbose:
        print(f"[+] AST built from {dsl_file}")

    # Stage 2: Build Semantic IR
    semantic_ir = SemanticScenario.from_ast(ast_scenario)
    if verbose:
        print(f"[+] Semantic IR built: {semantic_ir.name}")

    # Stage 3: Load bindings
    loader = BindingLoader()
    loader.load(binding_file)
    if verbose:
        print(f"[+] Loaded {len(loader.list_all_bindings())} bindings")

    # Stage 4: Map to Execution Plan
    mapper = ExecutionPlanMapper(loader)
    execution_plan = mapper.map_scenario(semantic_ir)
    if verbose:
        print(f"[+] Execution plan created with {len(execution_plan.bindings_used)} bound actions")

    # Stage 5: Execute with Mock Backend
    backend = MockBackend(seed=seed)
    tracer = ExecutionTracer(semantic_ir.name)
    tracer.start()

    for phase in execution_plan.phases:
        for child in phase.children:
            if hasattr(child, 'children'):
                # Nested phase
                for grandchild in child.children:
                    if hasattr(grandchild, 'dsl_action'):
                        result = backend.execute(
                            grandchild.backend_operation,
                            **{k: v.lstrip('$') for k, v in grandchild.inputs.items()}
                        )
                        tracer.record(
                            operation=grandchild.backend_operation,
                            inputs={k: v.lstrip('$') for k, v in grandchild.inputs.items()},
                            outputs=result.metrics,
                            status=result.status.value,
                            duration_ms=result.duration_ms
                        )
            elif hasattr(child, 'dsl_action'):
                # Top-level action
                result = backend.execute(
                    child.backend_operation,
                    **{k: v.lstrip('$') for k, v in child.inputs.items()}
                )
                tracer.record(
                    operation=child.backend_operation,
                    inputs={k: v.lstrip('$') for k, v in child.inputs.items()},
                    outputs=result.metrics,
                    status=result.status.value,
                    duration_ms=result.duration_ms
                )

    tracer.end()
    execution_trace = tracer.to_trace()
    if verbose:
        print(f"[+] Executed {len(execution_trace.steps)} steps")

    # Stage 6: Compile constraints from Semantic IR
    constraint_ir = compile_to_json(semantic_ir)
    if verbose:
        print(f"[+] Compiled {len(constraint_ir['constraints'])} constraints")

    # Stage 7: Validate with Checker
    result_tracker = E2EPipelineResult(semantic_ir.name)
    all_passed = True

    # Build constraint specs for validator
    # Constraint IR format: {'metric': ..., 'operator': 'in'/'==', 'value': {...}, 'anchor': 'end'}
    constraint_specs = []
    for c in constraint_ir['constraints']:
        # Determine constraint type from operator and value
        value = c['value']
        operator = c['operator']

        if isinstance(value, dict) and value.get('type') == 'range':
            constraint_type = ConstraintType.RANGE
        elif operator == '==' and isinstance(value, (str, int, float)):
            constraint_type = ConstraintType.EQUALITY
        else:
            # Default to equality for unknown formats
            constraint_type = ConstraintType.EQUALITY

        constraint_spec = ConstraintSpec(
            metric=c['metric'],
            constraint_type=constraint_type,
            value=value,
            anchor=c.get('anchor', 'end'),
            required=c.get('required', True)
        )
        constraint_specs.append(constraint_spec)

    # Get actual metrics from execution trace
    actual_metrics = {}
    for step in execution_trace.steps:
        actual_metrics.update(step.outputs)

    # Check each constraint against actual metrics
    for constraint in constraint_specs:
        actual_value = actual_metrics.get(constraint.metric)

        validation_result = ConstraintValidator.validate_value(actual_value, constraint)

        if not validation_result.passed:
            all_passed = False
            issue = ValidationIssue(
                metric=constraint.metric,
                expected=str(constraint.value),
                actual=str(actual_value),
                severity="error",
                description=f"Constraint failed: {validation_result.reason}"
            )
            result_tracker.add_violation(issue)
        elif verbose:
            print(f"    [OK] {constraint.metric}: {validation_result.reason}")

    # Set overall status
    if all_passed and len(execution_trace.steps) > 0:
        status = "pass"
    elif len(execution_trace.steps) == 0:
        status = "unknown"
    else:
        status = "fail"

    # Build final report
    report = {
        "scenario_name": semantic_ir.name,
        "status": status,
        "all_passed": all_passed,
        "constraints": constraint_ir['constraints'],
        "violations": [v.to_dict() for v in result_tracker.violations] if hasattr(result_tracker, 'violations') else [],
        "steps": [s.to_dict() for s in execution_trace.steps],
        "metrics": actual_metrics
    }

    if verbose:
        print(f"[*] Final status: {status}")
        print(f"    Steps: {len(execution_trace.steps)}")
        print(f"    Violations: {len(report['violations'])}")

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run E2E pipeline for OSC DSL scenarios')
    parser.add_argument('dsl_file', help='Path to the DSL file')
    parser.add_argument('-b', '--binding', help='Path to binding.yaml (default: look in compiler/bindings/)')
    parser.add_argument('-s', '--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('-o', '--output', help='Output file for final report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed output')

    args = parser.parse_args()

    # Determine binding file path
    if not args.binding:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_binding = os.path.join(script_dir, "binding.yaml")
        if os.path.exists(default_binding):
            args.binding = default_binding
        else:
            # Try parent directory
            parent_binding = os.path.join(script_dir, "..", "bindings", "binding.yaml")
            if os.path.exists(parent_binding):
                args.binding = parent_binding

    try:
        # Run E2E pipeline
        report = run_e2e_pipeline(
            dsl_file=args.dsl_file,
            binding_file=args.binding,
            seed=args.seed,
            verbose=args.verbose
        )

        # Output
        output = json.dumps(report, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Final report written to: {args.output}")
        else:
            print(output)

        # Return exit code based on status
        if report['all_passed'] and report['status'] != 'unknown':
            return 0
        else:
            return 1

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
