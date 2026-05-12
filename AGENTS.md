# Project: OSC DSL Compiler for Enterprise Network Simulation

## 1. Project Goal

Build a compiler that translates OpenSCENARIO-like DSL into:

* Semantic IR
* Execution Plan
* Runtime Checker Spec

The system targets **enterprise network simulation**, not autonomous driving.

---

## 2. Core Architecture Principles

1. The compiler is NOT a simulator
2. The compiler does NOT implement network protocols
3. The compiler produces:

   * IR (semantic)
   * Execution plan (backend-neutral)
   * Checker spec (acceptance + coverage)
4. Backend execution is handled by:

   * ns-3 / Mininet / lab / mock backend

---

## 3. DSL Semantic Model

### 3.1 Key Concepts

* Scenario = composition of actions
* Action = atomic behavior (non-decomposable)
* Actor = entity performing actions
* Event = time anchor (start/end)
* Constraint = condition over metrics
* Coverage = sampling requirement

### 3.2 Execution Semantics

* serial → ordered phases
* parallel → concurrent execution
* constraints are evaluated at anchors (start/end)
* coverage is evaluated at sampling events

---

## 4. IR Layers

The compiler MUST produce 3 IRs:

### Syntax IR

* close to AST

### Semantic IR

* scenario structure
* actors
* actions
* constraints
* events
* coverage

### Execution IR

* phases
* tasks
* backend operations
* acceptance rules

---

## 5. Action Binding

Actions are abstract and must be mapped via binding.yaml

Example:

laptop.scan_ssid → wifi.scan
laptop.authenticate → aaa.authenticate

The compiler MUST NOT hardcode backend logic.

---

## 6. Constraint & Coverage Rules

* `at: end` → constraint anchor
* `event: end` → coverage sampling point
* `keep(...)` → domain restriction (pre-generation)
* `cover(...)` → coverage goal (post-execution accumulation)

---

## 7. Compiler Responsibilities

### MUST do:

* parse DSL
* build AST
* build semantic IR
* build execution plan
* generate checker spec

### MUST NOT do:

* simulate network behavior
* implement protocol stack
* depend on specific backend

---

## 8. Project Structure

```
compiler/
├── parser/         # DSL parsing (lexer + recursive descent parser)
│   ├── __init__.py
│   ├── parser.py   # Lexer + Parser classes
│   └── test.py     # Parser tests
├── semantic/       # Symbol resolution & type checking
│   ├── __init__.py
│   └── symbol_table.py
├── ir/             # Intermediate representations
│   ├── __init__.py
│   ├── ast_nodes.py        # AST node definitions
│   ├── semantic_ir.py      # Semantic IR definitions + ConstraintSpec
│   ├── to_semantic_ir.py   # AST to Semantic IR converter
│   └── compile_constraints.py  # Constraint compilation CLI
├── lowering/       # IR transformations (not yet implemented)
│   └── __init__.py
├── runtime/        # Constraint evaluation (not yet implemented)
│   └── __init__.py
└── bindings/       # Action → backend mapping (not yet implemented)
    └── __init__.py

examples/           # OSC DSL example files
compiler/ir/
├── semantic_ir.json      # Generated Semantic IR output
└── constraint_ir.json    # Generated Constraint IR output
```

---

## 9. Coding Principles

* prioritize correctness over completeness
* prefer explicit IR over implicit logic
* separate parsing / semantics / execution
* keep backend decoupled
