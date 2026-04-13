# OSC DSL Compiler

A compiler for OpenSCENARIO-like DSL targeting enterprise network simulation.

## Overview

This compiler translates a domain-specific language (DSL) for network scenario definitions into intermediate representations (IR), execution plans, and runtime checker specifications. It is designed for **enterprise network simulation**, not autonomous driving.

**Key Principle**: The compiler produces artifacts for simulation backends - it does NOT simulate network behavior itself.

## Features

- **DSL Parser**: Lexer and recursive descent parser for OSC-like syntax
- **Semantic IR**: Structured representation of scenarios, actors, actions, constraints
- **Execution IR**: Backend-neutral execution plans with phases and tasks
- **Constraint IR**: Formal constraint specifications for validation
- **Action Binding**: Flexible mapping from DSL actions to backend operations
- **Checker Spec**: Runtime validation and coverage specifications
- **E2E Pipeline**: Complete compilation pipeline with mock backend support

## Architecture

```text
DSL Source → Parser → AST → Semantic IR → Execution IR → Checker Spec
                                         ↓
                                    Binding Mapping
                                         ↓
                                    Backend Execution
```

### IR Layers

1. **Syntax IR (AST)**: Close to source syntax
2. **Semantic IR**: Scenario structure, actors, actions, constraints, events, coverage
3. **Execution IR**: Phases, tasks, backend operations, acceptance rules

## Project Structure

```text
compiler/
├── parser/              # DSL parsing
│   ├── parser.py        # Lexer + Parser classes
│   └── test.py          # Parser tests
├── semantic/            # Symbol resolution
│   └── symbol_table.py  # Symbol table implementation
├── ir/                  # Intermediate representations
│   ├── ast_nodes.py     # AST node definitions
│   ├── semantic_ir.py   # Semantic IR definitions
│   ├── execution_ir.py  # Execution IR definitions
│   ├── to_semantic_ir.py    # AST → Semantic IR converter
│   └── generate_execution_plan.py  # Execution plan generator
│   └── compile_constraints.py      # Constraint compilation CLI
├── bindings/            # Action → backend mapping
│   ├── binding.yaml     # Binding configuration
│   ├── loader.py        # YAML loader
│   └── mapper.py        # Action mapper
├── runtime/             # Runtime validation
│   ├── checker_spec.py  # Checker spec definitions
│   └── validator.py     # Constraint validator
└── lowering/            # IR transformations
    ├── e2e_pipeline.py  # End-to-end pipeline
    ├── execute_scenario.py  # Scenario executor
    ├── mock_backend.py  # Mock backend implementation
    └── execution_trace.py   # Execution trace recorder

examples/                # OSC DSL example files
└── enterprise_wifi.osc  # Enterprise WiFi scenario
```

## DSL Example

```osc
scenario enterprise_wifi_session:
    worker: employee
    laptop: managed_laptop

    do serial():
        connect:
            parallel():
                laptop.scan_ssid() with:
                    signal_strength([-67..-55], at: end)

                laptop.authenticate() with:
                    auth_status(success, at: end)
                    auth_latency_ms([200..1500], at: end)
```

## Semantic Model

| Concept | Description |
|---------|-------------|
| Scenario | Composition of actions |
| Action | Atomic behavior (non-decomposable) |
| Actor | Entity performing actions |
| Event | Time anchor (start/end) |
| Constraint | Condition over metrics |
| Coverage | Sampling requirement |

## Execution Semantics

- `serial()` → Ordered phases
- `parallel()` → Concurrent execution
- Constraints evaluated at anchors (`at: start`, `at: end`)
- Coverage evaluated at sampling events

## Action Binding

Actions are abstract and mapped via `binding.yaml`:

```yaml
laptop.scan_ssid:
  backend: wifi.scan
  outputs: [signal_strength, ssid, channel]

laptop.authenticate:
  backend: aaa.authenticate
  outputs: [auth_status, auth_latency_ms]
```

## Generated Outputs

| File | Description |
|------|-------------|
| `semantic_ir.json` | Semantic IR representation |
| `constraint_ir.json` | Compiled constraints |
| `execution_plan.json` | Execution plan for backend |
| `checker_spec.json` | Runtime validation spec |
| `execution_trace.json` | Execution trace from backend |
| `final_report.json` | Validation results |

## Quick Start

```bash
# Parse DSL source
python -m compiler.parser.parser examples/enterprise_wifi.osc

# Generate Semantic IR
python compiler/ir/to_semantic_ir.py

# Compile constraints
python compiler/ir/compile_constraints.py

# Generate execution plan
python compiler/ir/generate_execution_plan.py

# Run E2E pipeline
python compiler/lowering/e2e_pipeline.py examples/enterprise_wifi.osc
```

## Design Principles

1. **Correctness over completeness** - Prioritize correct IR generation
2. **Explicit IR over implicit logic** - All transformations are visible
3. **Separation of concerns** - Parsing, semantics, execution are distinct
4. **Backend decoupling** - No dependency on specific simulation backend

## License

MIT
