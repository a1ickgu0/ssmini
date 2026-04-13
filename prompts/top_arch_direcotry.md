# Compiler Directory Responsibilities

This project is structured as a multi-stage compiler pipeline.
Each directory has a **strict responsibility boundary**.
Do NOT mix responsibilities across directories.

---

## 📁 compiler/parser/

### Responsibility

Parse DSL source code into AST (Abstract Syntax Tree).

### Must Do

* Tokenize DSL input
* Handle indentation / block structure
* Build AST nodes:

  * ScenarioNode
  * ActorNode
  * PhaseNode
  * ActionNode
  * ConstraintNode

### Must NOT Do

* No semantic validation
* No type checking
* No backend logic
* No execution logic

### Output

* AST (Python objects or JSON)

---

## 📁 compiler/semantic/

### Responsibility

Convert AST into **semantically valid model**

### Must Do

* Symbol resolution

  * actors
  * actions
  * variables
* Type checking
* Validate references
* Normalize constructs

  * serial / parallel
  * with blocks
  * implicit anchors

### Must NOT Do

* No execution planning
* No backend mapping
* No runtime evaluation

### Output

* Semantic Model (cleaned + validated AST)

---

## 📁 compiler/ir/

### Responsibility

Define all Intermediate Representations (IR)

### Must Do

Define 3 IR layers:

1. Syntax IR (optional, near AST)
2. Semantic IR

   * scenario structure
   * actors
   * phases
   * actions
   * constraints
   * events
3. Execution IR

   * phases
   * tasks
   * operations
   * acceptance rules

### Must NOT Do

* No parsing
* No backend mapping
* No execution

### Output

* JSON schemas + data classes

---

## 📁 compiler/lowering/

### Responsibility

Transform Semantic IR → Execution IR

### Must Do

* Convert:

  * actions → backend-neutral operations
  * constraints → acceptance rules
  * phases → execution schedule
* Apply action bindings (via bindings/)
* Normalize execution structure

### Must NOT Do

* No real execution
* No metric calculation
* No simulation

### Output

* execution_plan.json

---

## 📁 compiler/runtime/

### Responsibility

Evaluate execution results against constraints and coverage

### Must Do

* Validate:

  * equality constraints
  * range constraints
  * missing values
* Evaluate pass/fail
* Accumulate coverage (future extension)

### Must NOT Do

* No DSL parsing
* No IR building
* No backend execution logic

### Output

* checker_spec.json
* execution_result.json
* final_report.json

---

## 📁 compiler/bindings/

### Responsibility

Define mapping between DSL actions and backend operations

### Must Do

* Provide mapping rules:

  * DSL action → backend operation
* Define:

  * input parameters
  * output metrics

### Example

laptop.scan_ssid → wifi.scan
laptop.authenticate → aaa.authenticate

### Must NOT Do

* No logic execution
* No simulation
* No parsing

### Output

* binding.yaml
* loaded mapping objects

---

# 🔥 Critical Design Rule

Each layer must be:

* **Pure**
* **Single responsibility**
* **Composable**

Pipeline:

DSL → parser → semantic → IR → lowering → runtime

---

# ❌ Forbidden

* DO NOT mix parser + semantic
* DO NOT embed backend logic in compiler
* DO NOT evaluate constraints during parsing
* DO NOT hardcode action behavior outside bindings

---

# ✅ Goal

Make the compiler:

* deterministic
* debuggable
* backend-independent
* extensible
